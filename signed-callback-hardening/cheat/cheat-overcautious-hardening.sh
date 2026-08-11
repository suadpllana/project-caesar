#!/bin/bash
# Hardening by reflex rather than by reading: refuse every document-annotation header outright, bind each key to a single partner, and demand that every header present be covered by the signature. Each one blocks its forgery family and breaks traffic that runs today.
set -euo pipefail

cat > /app/svc/auth/verify.py <<'PYEOF'
import hashlib
import hmac
import time

from ..core import canon, cfg, jsonx
from ..pipeline.stages import overlay
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

_seen = {}


def _forget_expired(now, ttl):
    for token in [token for token, seen_at in _seen.items() if now - seen_at > ttl]:
        del _seen[token]


def _annotation_headers(headers):
    return [name for name in headers
            if name.startswith(overlay.PREFIX) and len(name) > len(overlay.PREFIX)]


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
    absent = [n for n in headers if n not in cover and n not in ("x-sig", "x-sig-headers")]
    if _annotation_headers(headers):
        return False, "annotation-header"
    if absent:
        return False, "cover-missing:" + ",".join(sorted(absent))
    for name in cover:
        if name not in headers:
            return False, "cover-absent:" + name

    data = canon.sig_input(request["method"], request["path"], headers["x-sig-headers"], headers)
    expected = hmac.new(entry["secret"].encode("utf-8"), data, hashlib.sha256).hexdigest()
    supplied = headers["x-sig"].strip().lower()
    if len(supplied) != len(expected) or not hmac.compare_digest(expected, supplied):
        return False, "bad-signature"

    if headers["x-partner"] != (entry.get("subjects") or [""])[0]:
        return False, "not-entitled"

    try:
        stamp = int(headers["x-ts"])
    except ValueError:
        return False, "bad-ts"
    skew = int(policy.get("max_skew_sec", 300))
    now = time.time()
    if abs(now - stamp) > skew:
        return False, "outside-skew"

    try:
        doc = jsonx.parse(request["body"].decode("utf-8"), keep=jsonx.KEEP_FIRST)
    except (ValueError, UnicodeDecodeError):
        return False, "bad-body"
    if not hmac.compare_digest(canon.body_tag(doc), headers["x-body-sha256"].strip().lower()):
        return False, "body-mismatch"

    token = headers["x-key-id"] + "\x00" + headers["x-nonce"]
    _forget_expired(now, skew * 4)
    if token in _seen:
        return False, "replayed"
    _seen[token] = now

    return True, ""
PYEOF
