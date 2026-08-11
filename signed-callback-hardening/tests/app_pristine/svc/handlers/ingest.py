from ..core import store
from ..pipeline import chain
from ..pipeline.errors import Halt


def apply(headers, raw):
    try:
        state = chain.run(headers, raw)
    except Halt as halt:
        return halt.code, halt.payload

    doc = state["doc"]
    if not isinstance(doc, dict):
        return 400, {"status": "bad-document"}

    seq = store.append(
        {
            "partner": headers.get("x-partner", ""),
            "target": headers.get("x-target", ""),
            "nonce": headers.get("x-nonce", ""),
            "labels": state["labels"],
            "doc": doc,
        }
    )
    return 200, {"status": "stored", "seq": seq}
