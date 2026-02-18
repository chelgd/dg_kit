import json, boto3, pickle
from typing import Any, Dict, Optional

from .local import LocalArtifact

from io import BytesIO
from botocore.exceptions import ClientError


class S3Artifact(LocalArtifact):
    def __init__(
        self,
        base_object,
        config: Dict,
        s3_credentials: Optional[Dict[str, str]],
        s3_bucket,
        ):
        self.base_object = base_object
        self.config = config
        self.buffer = BytesIO()
        self.s3_credentials = s3_credentials
        self.s3_bucket = s3_bucket

    def serialize(self):
        serialized_artifact = pickle.dumps(self.base_object) #self.base_object._serialize_model()
        self.buffer = BytesIO(serialized_artifact)

    def deserialize(self):
        if not hasattr(self, "buffer") or self.buffer is None:
            raise ValueError("No buffer to deserialize from")

        self.buffer.seek(0)
        self.serialized_artifact = pickle.loads(self.buffer.read())
        return self.serialized_artifact

    def save_to_s3(self):
        """
        Upload all artifact files in the current directory to an S3 location.

        :param s3_uri: Target S3 URI in the format ``s3://bucket/prefix/``.
        :type s3_uri: str

        :raises botocore.exceptions.BotoCoreError: If an S3 upload fails.
        :raises ValueError: If ``s3_uri`` is not a valid S3 path.
        """
        self.serialize()

        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.s3_credentials["aws_access_key_id"],
            aws_secret_access_key=self.s3_credentials["aws_secret_access_key"],
        )

        # ensure a "folder" (prefix) exists by creating a zero-byte object with a trailing slash
        original_name = self.config['name']
        try:
            s3.put_object(Bucket=self.s3_bucket, Key=f"{original_name}/")
        except Exception:
            pass

        # reset buffer before upload
        self.buffer.seek(0)

        # adjust model_name so the subsequent upload_fileobj places the file under the folder
        self.model_path = f"{original_name}/{original_name}"

        s3.upload_fileobj(self.buffer, self.s3_bucket, self.model_path + self.get_model_file_extension())
        # upload model params/ config as JSON into the same "folder" on S3
        params = getattr(self, "model_params", getattr(self, "model_config", None))
        if params is not None:
            body = json.dumps(params, default=str).encode("utf-8")
            s3.put_object(
                Bucket=self.s3_bucket,
                Key=f"{original_name}/model_params.json",
                Body=body,
                ContentType="application/json",
            )

    def load_from_s3(self):
        """
        Download artifact metadata and preprocessor files from S3.

        :param s3_uri: S3 URI where the artifact is stored, e.g. ``s3://bucket/prefix/``.
        :type s3_uri: str
        
        :param local_dir: Local directory where the files should be downloaded.
        :type local_dir: str

        :raises botocore.exceptions.BotoCoreError: If the download fails.
        :raises FileNotFoundError: If specified S3 keys do not exist.
        """
        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.s3_credentials["aws_access_key_id"],
            aws_secret_access_key=self.s3_credentials["aws_secret_access_key"],
        )

        # construct the expected S3 key using the same convention as save_to_s3
        ext = self.get_model_file_extension()
        key = f"{self.config['name']}/{self.config['name']}{ext}"

        try:
            resp = s3.get_object(Bucket=self.s3_bucket, Key=key)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404", "NotFound"):
                raise FileNotFoundError(f"S3 object s3://{self.s3_bucket}/{key} not found") from e
            raise

        # read object into the in-memory buffer and prepare for deserialization
        data = resp["Body"].read()
        self.buffer = BytesIO(data)
        self.buffer.seek(0)

        try:
            # subclass should implement deserialize to populate self.base_object from buffer
            self.deserialize()
        except Exception as e:
            raise RuntimeError("Failed to deserialize model loaded from S3") from e
        
        # attempt to load model params/config JSON from the same S3 "folder"
        params_key = f"{self.config['name']}/model_params.json"
        try:
            resp = s3.get_object(Bucket=self.s3_bucket, Key=params_key)
            body = resp["Body"].read()
            if body:
                params = json.loads(body.decode("utf-8"))
            # set both names for compatibility
            self.model_params = params
            self.model_config = getattr(self, "model_config", None) or params
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            # ignore missing params file, re-raise other errors
            if code not in ("NoSuchKey", "404", "NotFound"):
                raise FileNotFoundError(f"S3 object s3://{self.s3_bucket}/{key} not found") from e
            raise

        return getattr(self, "base_object", None)