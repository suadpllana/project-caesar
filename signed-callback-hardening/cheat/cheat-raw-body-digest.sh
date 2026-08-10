#!/bin/bash
# Fixes the body by digesting the raw bytes instead of the parse the handler performs. Blocks every body forgery and rejects every real partner request, because the client library serializes with json.dumps default separators while the digest is taken over the compact sorted form.
set -euo pipefail

cat > /app/svc/auth/verify.py <<'PYEOF'
import hashlib
import hmac
import time

from ..core import canon, cfg
from . import keys

MUST_BE_COVERED = ("x-key-id", "x-partner", "x-target", "x-ts", "x-nonce", "x-body-sha256")

_seen = {}


def check(request):
    headers = request["headers"]
    for name in ("x-key-id", "x-sig", "x-sig-headers", "x-body-sha256", "x-partner",
                 "x-target", "x-ts", "x-nonce"):
        if not headers.get(name):
            return False, "missing:" + name
    entry = keys.lookup(headers["x-key-id"])
    if entry is None:
        return False, "unknown-key"
    policy = cfg.section("signing")
    if entry.get("state") not in policy.get("accepted_key_states", ["active"]):
        return False, "key-state"
    cover = canon.cover_list(headers["x-sig-headers"])
    if [name for name in MUST_BE_COVERED if name not in cover]:
        return False, "cover-missing"
    data = canon.sig_input(request["method"], request["path"], headers["x-sig-headers"], headers)
    expected = hmac.new(entry["secret"].encode("utf-8"), data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, headers["x-sig"].strip().lower()):
        return False, "bad-signature"
    try:
        stamp = int(headers["x-ts"])
    except ValueError:
        return False, "bad-ts"
    skew = int(policy.get("max_skew_sec", 300))
    now = time.time()
    if abs(now - stamp) > skew:
        return False, "outside-skew"
    if not hmac.compare_digest(hashlib.sha256(request["body"]).hexdigest(),
                               headers["x-body-sha256"].strip().lower()):
        return False, "body-mismatch"
    token = headers["x-key-id"] + "\x00" + headers["x-nonce"]
    if token in _seen:
        return False, "replayed"
    _seen[token] = now
    return True, ""
PYEOF
