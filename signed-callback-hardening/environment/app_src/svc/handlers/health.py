from ..core import cfg


def probe(headers, raw):
    return 200, {"status": "ok", "profile": cfg.active_profile()}
