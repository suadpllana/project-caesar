import hashlib
import hmac
import json
import os
import time

DEFAULT_METHOD = "POST"
DEFAULT_PATH = "/v1/callback"
BASE_COVER = ["x-key-id", "x-partner", "x-target", "x-ts", "x-nonce", "x-body-sha256"]
EXTRA_COVER = ["x-ctx", "x-trace"]
DOC_PREFIX = "x-doc-"


def body_bytes(doc):
    return json.dumps(doc, ensure_ascii=False).encode("utf-8")


def body_tag(doc):
    packed = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()


def new_nonce():
    return os.urandom(12).hex()


def sign(
    secret,
    key_id,
    partner,
    target,
    doc,
    ctx=None,
    trace=None,
    doc_headers=None,
    ts=None,
    nonce=None,
    cover=None,
    method=DEFAULT_METHOD,
    path=DEFAULT_PATH,
):
    body = body_bytes(doc)
    headers = {
        "x-key-id": key_id,
        "x-partner": partner,
        "x-target": target,
        "x-ts": str(int(ts if ts is not None else time.time())),
        "x-nonce": nonce if nonce is not None else new_nonce(),
        "x-body-sha256": body_tag(doc),
    }
    if ctx is not None:
        headers["x-ctx"] = ctx
    if trace is not None:
        headers["x-trace"] = trace
    for field, value in sorted((doc_headers or {}).items()):
        headers[DOC_PREFIX + field.replace("_", "-")] = str(value)

    if cover is None:
        cover = (
            list(BASE_COVER)
            + [name for name in EXTRA_COVER if name in headers]
            + sorted(name for name in headers if name.startswith(DOC_PREFIX))
        )
    spec = ";".join(cover)
    headers["x-sig-headers"] = spec

    rows = [method.upper(), path, spec]
    for name in cover:
        rows.append(name + ":" + headers.get(name, ""))
    headers["x-sig"] = hmac.new(
        secret.encode("utf-8"), "\n".join(rows).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return headers, body
