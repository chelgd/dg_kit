import pickle
from typing import Dict

class LocalArtifact:
    def __init__(
        self,
        base_object,
        config: Dict,
    ):
        self.base_object = base_object
        self.config = config
    
    def save_to_local(self):
        with open(f"{self.config['data_catalog']['dc_checkpoint_path']}/{self.config['name']}.pkl", "wb") as f:
            pickle.dump(self.base_object, f)

    def load_from_local(self):
        with open(f"{self.config['dc_checkpoint_path']}/{self.config['name']}.pkl", "rb") as f:
            self.base_object = pickle.load(f)
