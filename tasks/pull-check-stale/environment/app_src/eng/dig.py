import hashlib


def of(text):
    return hashlib.blake2s(text.encode("utf-8"), digest_size=4).hexdigest()


def mix(vals):
    h = hashlib.blake2s(digest_size=3)
    for v in vals:
        h.update(v.encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()
