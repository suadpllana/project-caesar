import hashlib
import hmac
import json

from ..core import canon
from . import keys

REQUIRED_HEADERS = ("x-key-id", "x-sig", "x-sig-headers", "x-body-sha256")


def check(request):
    headers = request["headers"]
    for name in REQUIRED_HEADERS:
        if not headers.get(name):
            return False, "missing:" + name

    entry = keys.lookup(headers["x-key-id"])
    if entry is None:
        return False, "unknown-key"

    data = canon.sig_input(request["method"], request["path"], headers["x-sig-headers"], headers)
    expected = hmac.new(entry["secret"].encode("utf-8"), data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, headers["x-sig"].strip()):
        return False, "bad-signature"

    try:
        doc = json.loads(request["body"].decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return False, "bad-body"
    if not hmac.compare_digest(canon.body_tag(doc), headers["x-body-sha256"].strip()):
        return False, "body-mismatch"

    return True, ""
