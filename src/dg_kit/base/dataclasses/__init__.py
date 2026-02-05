import hashlib


def id_generator(*parts: str, size: int = 16) -> str:
    h = hashlib.blake2b(digest_size=size)
    h.update("\x1f".join(parts).encode("utf-8"))
    return h.hexdigest()
