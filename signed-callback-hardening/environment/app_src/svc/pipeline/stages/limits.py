from ...core import cfg
from ..errors import Halt


def apply(state):
    limits = cfg.section("ingest")
    if len(state["raw"]) > int(limits.get("max_body_bytes", 65536)):
        raise Halt(413, {"status": "too-large"})
