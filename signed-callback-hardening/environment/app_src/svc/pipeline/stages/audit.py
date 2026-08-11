from ...auth import keys


def apply(state):
    entry = keys.lookup(state["headers"].get("x-key-id", "")) or {}
    state["labels"]["issued_to"] = ",".join(entry.get("subjects", []))
    state["labels"]["stage_count"] = str(len(state["labels"]) + 1)
