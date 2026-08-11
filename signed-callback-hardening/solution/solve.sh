#!/bin/bash
# Reference solution.
#
# The shipped verify.py already contains the whole textbook plan: presence checks, a
# floor on the covered-header set, the key-state policy from the live profile, a
# constant-time signature comparison, and a body digest taken with the project's own
# parser. Reading it produces no finding. The gaps are all in what happens to a request
# after verification returns, so the work is tracing the pipeline:
#
#   - /app/svc/handlers/ingest.py no longer parses anything itself. It runs
#     /app/svc/pipeline/chain.py, whose stage list comes from the live profile in
#     /app/svc/conf/profiles/standard.toml.
#   - The decode stage parses the body with jsonx.KEEP_FIRST, while canon.document -
#     what verify.py digests - uses the parser's default, KEEP_LAST. A repeated key at
#     the front of the document leaves the digest untouched and changes what the handler
#     receives.
#   - The overlay stage merges every x-doc-* header into the document. Those headers are
#     optional, so the covered-set floor does not reach them: a relay can add one to any
#     request and write a field the key holder never signed. Partners that do send them
#     have them covered, so the rule is "covered if present", not "absent".
#   - /app/svc/auth/keys.py records which partners each key is issued to, and the audit
#     stage reads it, but verification never does. Any active key can speak for any
#     partner. One key is issued to two partners, so binding a key to a single partner
#     would break real traffic.
#   - Freshness and replay were never implemented at all.
#
# After writing the file this script exercises it the way the author did: legitimate
# traffic through the real WSGI app, then one forgery per gap, failing loudly if any of
# them behaves the wrong way.

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
    absent = [name for name in MUST_BE_COVERED if name not in cover]
    absent += [name for name in _annotation_headers(headers) if name not in cover]
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

    if headers["x-partner"] not in (entry.get("subjects") or []):
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


nonce_seq = 0


def fresh():
    global nonce_seq
    nonce_seq += 1
    return "n-%d-%d" % (int(time.time()), nonce_seq)


def build(key_id="k-beta-1", partner="pt-beta", target="settle", doc=None, **kw):
    doc = doc if doc is not None else {"account": "ac-9912", "amount": 1750, "memo": "regular"}
    kw.setdefault("nonce", fresh())
    return signer.sign(secret(key_id), key_id, partner, target, doc, **kw)


# legitimate traffic, including relay headers and a partner-chosen cover order
for index in range(20):
    headers, body = build(ctx="region:eu;tier:gold")
    headers["x-relay-hop"] = "edge-2"
    expect("legitimate #%d" % index, 200, call(headers, body)[0])

headers, body = build(cover=["x-nonce", "x-body-sha256", "x-target", "x-key-id", "x-ts", "x-partner"])
expect("reordered cover list", 200, call(headers, body)[0])

# a key issued to several partners works for each of them
for partner in keys.lookup("k-relay-2")["subjects"]:
    headers, body = build(key_id="k-relay-2", partner=partner)
    expect("aggregator key for %s" % partner, 200, call(headers, body)[0])

# document annotations the partner signed are honored, and reach the handler
store.clear()
headers, body = build(doc_headers={"channel": "bulk"})
expect("signed annotation", 200, call(headers, body)[0])
if not store.entries() or store.entries()[-1]["doc"].get("channel") != "bulk":
    FAILURES.append("signed annotation never reached the handler")

# an annotation the relay adds is not covered by the signature
headers, body = build()
headers["x-doc-amount"] = "999999"
expect("relay annotation", 401, call(headers, body)[0])

# a repeated key at the front of the document: same digest, different decoded document
headers, body = build()
expect("front repeated key", 401, call(headers, b'{"amount": 99999, ' + body[1:].lstrip())[0])

doc = {"ref": "r-1", "order": {"account": "ac-1", "amount": 5}, "note": "n"}
headers, body = build(doc=doc)
text = body.decode("utf-8")
cut = text.index('"order": {') + len('"order": {')
expect("nested repeated key", 401,
       call(headers, (text[:cut] + '"amount": 91000, ' + text[cut:]).encode("utf-8"))[0])

# a key may only speak for the partners it was issued to
headers, body = build(key_id="k-beta-1", partner="pt-alpha")
expect("key speaking for another partner", 401, call(headers, body)[0])

# fields left outside the cover list must not be mutable afterwards
for name, value in (("x-partner", "pt-epsilon"), ("x-target", "notify"), ("x-nonce", fresh())):
    cover = [c for c in signer.BASE_COVER if c != name]
    headers, body = build(cover=cover)
    headers[name] = value
    expect("uncovered %s" % name, 401, call(headers, body)[0])

cover = [c for c in signer.BASE_COVER if c != "x-body-sha256"]
headers, body = build(cover=cover)
swap = {"account": "ac-0001", "amount": 999999}
headers["x-body-sha256"] = signer.body_tag(swap)
expect("uncovered body digest", 401, call(headers, signer.body_bytes(swap))[0])

# replay, clock skew and key policy
headers, body = build()
expect("first delivery", 200, call(headers, body)[0])
expect("replayed delivery", 401, call(headers, body)[0])

expect("stale request", 401, call(*build(ts=int(time.time()) - 4000))[0])
expect("future request", 401, call(*build(ts=int(time.time()) + 4000))[0])

for key_id in ("k-alpha-1", "k-gamma-0", "k-delta-1"):
    entry = keys.lookup(key_id)
    headers, body = build(key_id=key_id, partner=entry["subjects"][0])
    expect("state of %s" % key_id, 401, call(headers, body)[0])
for key_id in ("k-alpha-2", "k-beta-1", "k-epsilon-1"):
    entry = keys.lookup(key_id)
    headers, body = build(key_id=key_id, partner=entry["subjects"][0])
    expect("state of %s" % key_id, 200, call(headers, body)[0])

# two keys are allowed to pick the same nonce
shared = fresh()
expect("shared nonce, key one", 200, call(*build(key_id="k-beta-1", nonce=shared))[0])
expect("shared nonce, key two", 200,
       call(*build(key_id="k-alpha-2", partner="pt-alpha", nonce=shared))[0])

print("ledger entries: %d" % len(store.entries()))
if FAILURES:
    for line in FAILURES:
        print("FAIL " + line)
    sys.exit(1)
print("all reference checks passed")
PYEOF

python3 /tmp/exercise.py
rm -f /tmp/exercise.py
