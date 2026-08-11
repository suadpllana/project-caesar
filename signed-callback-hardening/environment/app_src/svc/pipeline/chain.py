from ..core import cfg
from .stages import audit, decode, limits, overlay

REGISTRY = {
    "limits": limits,
    "decode": decode,
    "overlay": overlay,
    "audit": audit,
}


def stage_names():
    return [str(name) for name in cfg.section("pipeline").get("stages", [])]


def run(headers, raw):
    state = {"headers": headers, "raw": raw, "doc": None, "labels": {}}
    for name in stage_names():
        stage = REGISTRY.get(name)
        if stage is None:
            continue
        stage.apply(state)
    return state
