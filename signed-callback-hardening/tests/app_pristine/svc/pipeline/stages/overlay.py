PREFIX = "x-doc-"


def field_name(header_name):
    return header_name[len(PREFIX):].replace("-", "_")


def apply(state):
    doc = state["doc"]
    if not isinstance(doc, dict):
        return
    for name in sorted(state["headers"]):
        if name.startswith(PREFIX) and len(name) > len(PREFIX):
            doc[field_name(name)] = state["headers"][name]
