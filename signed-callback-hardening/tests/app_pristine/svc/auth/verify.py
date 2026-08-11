import hashlib
import hmac

from ..core import canon, cfg
from . import keys

REQUIRED_HEADERS = (
    "x-key-id",
    "x-sig",
    "x-sig-headers",
    "x-body-sha256",
    "x-partner",
    "x-target",
    "x-ts",
    "x-nonce",
)

MUST_BE_COVERED = (
    "x-key-id",
    "x-partner",
    "x-target",
    "x-ts",
    "x-nonce",
    "x-body-sha256",
)


def check(request):
    headers = request["headers"]
    for name in REQUIRED_HEADERS:
        if not headers.get(name):
            return False, "missing:" + name

    entry = keys.lookup(headers["x-key-id"])
    if entry is None:
        return False, "unknown-key"

    policy = cfg.section("signing")
    if entry.get("state") not in policy.get("accepted_key_states", ["active"]):
        return False, "key-state"

    cover = canon.cover_list(headers["x-sig-headers"])
    if len(set(cover)) != len(cover):
        return False, "cover-repeated"
    absent = [name for name in MUST_BE_COVERED if name not in cover]
    if absent:
        return False, "cover-missing:" + ",".join(absent)
    for name in cover:
        if name not in headers:
            return False, "cover-absent:" + name

    data = canon.sig_input(request["method"], request["path"], headers["x-sig-headers"], headers)
    expected = hmac.new(entry["secret"].encode("utf-8"), data, hashlib.sha256).hexdigest()
    supplied = headers["x-sig"].strip().lower()
    if len(supplied) != len(expected) or not hmac.compare_digest(expected, supplied):
        return False, "bad-signature"

    try:
        doc = canon.document(request["body"])
    except (ValueError, UnicodeDecodeError):
        return False, "bad-body"
    if not hmac.compare_digest(canon.body_tag(doc), headers["x-body-sha256"].strip().lower()):
        return False, "body-mismatch"

    return True, ""
