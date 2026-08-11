from ...core import jsonx
from ..errors import Halt


def apply(state):
    try:
        state["doc"] = jsonx.parse(state["raw"].decode("utf-8"), keep=jsonx.KEEP_FIRST)
    except (ValueError, UnicodeDecodeError):
        raise Halt(400, {"status": "bad-document"})
    if not isinstance(state["doc"], dict):
        raise Halt(400, {"status": "bad-document"})
