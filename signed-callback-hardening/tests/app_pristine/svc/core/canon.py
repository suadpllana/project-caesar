import hashlib
import json


def body_bytes(doc):
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def body_tag(doc):
    return hashlib.sha256(body_bytes(doc)).hexdigest()


def cover_list(spec):
    return [name.strip().lower() for name in spec.split(";") if name.strip()]


def sig_input(method, path, spec, headers):
    rows = [method.upper(), path, spec]
    for name in cover_list(spec):
        rows.append(name + ":" + headers.get(name, ""))
    return "\n".join(rows).encode("utf-8")
