#!/bin/bash
# Reference solution.
#
# The work is a review of the whole request path, not of verify.py on its own:
#   - /app/sdk/signer.py fixes what legitimate traffic looks like, so the cover list is
#     partner-chosen and the body on the wire is not the canonical serialization the
#     digest is taken over. Anything that re-derives the digest from the raw bytes, or
#     that demands every header be covered, breaks partners that work today.
#   - /app/svc/handlers/ingest.py hands the body to /app/svc/core/jsonx.py, whose object
#     parser keeps the FIRST occurrence of a repeated key, while the shipped verifier
#     digests json.loads() output, which keeps the LAST. A repeated key placed at the
#     front of the document therefore leaves the digest untouched and changes what the
#     handler acts on. The fix is to take the digest over the parse the handler uses.
#   - /app/svc/conf/profiles/standard.toml is the profile /app/svc/core/cfg.py loads by
#     default; it names the key states allowed to sign and the clock tolerance.
#
# After writing the file this script exercises it the way the author did: legitimate
# traffic through the real WSGI app, then one forgery per bug class, failing loudly if
# any of them behaves the wrong way.

set -euo pipefail

cat > /app/svc/auth/verify.py <<'PYEOF'
import hashlib
import hmac
import time

from ..core import canon, cfg, jsonx
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


def check(request):
    headers = request["headers"]
    for name in REQUIRED_HEADERS:
        if not headers.get(name):
            return False, "missing:" + name

    entry = keys.lookup(headers["x-key-id"])
    if entry is None:
        return False, "unknown-key"

    policy = cfg.section("signing")
    allowed_states = policy.get("accepted_key_states", ["active"])
    if entry.get("state") not in allowed_states:
        return False, "key-state:" + str(entry.get("state"))

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
        stamp = int(headers["x-ts"])
    except ValueError:
        return False, "bad-ts"
    skew = int(policy.get("max_skew_sec", 300))
    now = time.time()
    if abs(now - stamp) > skew:
        return False, "outside-skew"

    try:
        doc = jsonx.parse(request["body"].decode("utf-8"))
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

cat > /tmp/exercise.py <<'PYEOF'
import io
import json
import sys
import time

sys.path.insert(0, "/app")

from sdk import signer
from svc import wsgi
from svc.auth import keys
from svc.core import store

FAILURES = []


def call(headers, body):
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/v1/callback",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    for name, value in headers.items():
        environ["HTTP_" + name.upper().replace("-", "_")] = value
    captured = {}

    def start_response(status, response_headers):
        captured["status"] = status

    chunks = wsgi.app(environ, start_response)
    return int(captured["status"].split()[0]), json.loads(b"".join(chunks).decode("utf-8"))


def expect(label, want, got):
    if want != got:
        FAILURES.append("%s: expected %s, got %s" % (label, want, got))


def secret(key_id):
    return keys.lookup(key_id)["secret"]


def build(key_id="k-beta-1", partner="pt-beta", target="settle", doc=None, **kw):
    doc = doc if doc is not None else {"account": "ac-9912", "amount": 1750, "memo": "regular"}
    return signer.sign(secret(key_id), key_id, partner, target, doc, **kw)


nonce = 0


def fresh():
    global nonce
    nonce += 1
    return "n-%d-%d" % (int(time.time()), nonce)


# legitimate traffic, including relay headers and a partner-chosen cover order
for index in range(25):
    headers, body = build(nonce=fresh(), ctx="region:eu;tier:gold")
    headers["x-relay-hop"] = "edge-2"
    expect("legitimate #%d" % index, 200, call(headers, body)[0])

headers, body = build(nonce=fresh(),
                      cover=["x-nonce", "x-body-sha256", "x-target", "x-key-id", "x-ts", "x-partner"])
expect("reordered cover list", 200, call(headers, body)[0])

# a repeated key at the front of the document: same json.loads reading, different
# reading for the parser the ingest handler uses
headers, body = build(nonce=fresh())
forged = b'{"amount": 99999, ' + body[1:].lstrip()
expect("front repeated key", 401, call(headers, forged)[0])

# the same trick inside a nested object
doc = {"ref": "r-1", "order": {"account": "ac-1", "amount": 5}, "note": "n"}
headers, body = build(doc=doc, nonce=fresh())
text = body.decode("utf-8")
cut = text.index('"order": {') + len('"order": {')
expect("nested repeated key", 401,
       call(headers, (text[:cut] + '"amount": 91000, ' + text[cut:]).encode("utf-8"))[0])

# fields left outside the cover list must not be mutable afterwards
for name, mutate in (
    ("x-partner", lambda h: h.__setitem__("x-partner", "pt-alpha")),
    ("x-target", lambda h: h.__setitem__("x-target", "notify")),
    ("x-nonce", lambda h: h.__setitem__("x-nonce", fresh())),
    ("x-ts", lambda h: h.__setitem__("x-ts", str(int(time.time())))),
):
    cover = [c for c in signer.BASE_COVER if c != name]
    headers, body = build(nonce=fresh(), cover=cover)
    mutate(headers)
    expect("uncovered %s" % name, 401, call(headers, body)[0])

cover = [c for c in signer.BASE_COVER if c != "x-body-sha256"]
headers, body = build(nonce=fresh(), cover=cover)
swap = {"account": "ac-0001", "amount": 999999}
headers["x-body-sha256"] = signer.body_tag(swap)
expect("uncovered body digest", 401, call(headers, signer.body_bytes(swap))[0])

# replay, clock skew and key policy
headers, body = build(nonce=fresh())
expect("first delivery", 200, call(headers, body)[0])
expect("replayed delivery", 401, call(headers, body)[0])

headers, body = build(nonce=fresh(), ts=int(time.time()) - 4000)
expect("stale request", 401, call(headers, body)[0])
headers, body = build(nonce=fresh(), ts=int(time.time()) + 4000)
expect("future request", 401, call(headers, body)[0])

for key_id in ("k-alpha-1", "k-gamma-0", "k-delta-1"):
    headers, body = build(key_id=key_id, nonce=fresh())
    expect("state of %s" % key_id, 401, call(headers, body)[0])
for key_id in ("k-alpha-2", "k-beta-1", "k-gamma-2", "k-epsilon-1"):
    headers, body = build(key_id=key_id, nonce=fresh())
    expect("state of %s" % key_id, 200, call(headers, body)[0])

# two partners are allowed to pick the same nonce
shared = fresh()
expect("shared nonce, key one", 200, call(*build(key_id="k-beta-1", nonce=shared))[0])
expect("shared nonce, key two", 200, call(*build(key_id="k-alpha-2", nonce=shared))[0])

print("ledger entries: %d" % len(store.entries()))
if FAILURES:
    for line in FAILURES:
        print("FAIL " + line)
    sys.exit(1)
print("all reference checks passed")
PYEOF

python3 /tmp/exercise.py
rm -f /tmp/exercise.py
