"""Shared machinery for the verifier.

Everything here drives the *composed* service: the pristine application tree that this
image bakes at /app, with the agent's /app/svc/auth/verify.py dropped in on top by the
harness. Requests go through /app/svc/wsgi.py exactly as they would over the wire, so a
test observes what the whole pipeline did, not what one function returned.
"""

import io
import json
import os
import random
import sys

APP_ROOT = "/app"
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from sdk import signer  # noqa: E402
from svc import wsgi  # noqa: E402
from svc.auth import keys  # noqa: E402
from svc.core import cfg, store  # noqa: E402

# The verifier derives its expectations from the service's own configuration and key
# store rather than hardcoding them, so the task and the tests cannot drift apart.
SIGNING = cfg.section("signing")
MAX_SKEW_SEC = int(SIGNING.get("max_skew_sec", 300))
ACCEPTED_KEY_STATES = list(SIGNING.get("accepted_key_states", ["active"]))

SIGNING_KEYS = [k for k in keys.ids() if keys.lookup(k)["state"] in ACCEPTED_KEY_STATES]
NON_SIGNING_KEYS = [k for k in keys.ids() if keys.lookup(k)["state"] not in ACCEPTED_KEY_STATES]

PARTNERS = ["pt-alpha", "pt-beta", "pt-gamma", "pt-delta", "pt-epsilon"]
STORING_TARGETS = ["settle", "notify"]

# Headers a relaying intermediary adds on the way through. Partners never sign these,
# so a solution that demands total header coverage fails the legitimate-traffic test.
RELAY_HEADERS = ["x-relay-hop", "x-forwarded-for", "x-received-at", "x-relay-attempt"]

ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789-_"
WIDE_CHARS = "aeiouéüñå中文λ"


def secret_for(key_id):
    return keys.lookup(key_id)["secret"]


def call(headers, body, method="POST", path="/v1/callback"):
    """Send one request through the WSGI application and return (status_code, payload)."""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    for name, value in headers.items():
        environ["HTTP_" + name.upper().replace("-", "_")] = value

    captured = {}

    def start_response(status, response_headers):
        captured["status"] = status

    chunks = wsgi.app(environ, start_response)
    payload = json.loads(b"".join(chunks).decode("utf-8"))
    return int(captured["status"].split()[0]), payload


def deliver(headers, body, method="POST", path="/v1/callback"):
    """Send a request and report what the pipeline recorded because of it.

    Returns (status_code, payload, new_records). new_records is what the ingest handler
    appended to the ledger during this request, which is the observable effect an
    attacker is trying to produce.
    """
    before = len(store.entries())
    status, payload = call(headers, body, method=method, path=path)
    return status, payload, store.entries()[before:]


def text(rng, length=8, wide=False):
    pool = WIDE_CHARS if wide else ALPHABET
    return "".join(rng.choice(pool) for _ in range(length))


def document(rng, depth=0):
    """A callback document with the shapes real partner payloads have.

    Never emits a repeated key: legitimate traffic is well formed, and the tests that
    exercise malformed traffic build it explicitly.
    """
    doc = {}
    for _ in range(rng.randint(2, 6)):
        key = text(rng, rng.randint(3, 10))
        roll = rng.random()
        if roll < 0.22:
            doc[key] = rng.randint(-10 ** 7, 10 ** 7)
        elif roll < 0.36:
            doc[key] = round(rng.uniform(-5000, 5000), 6)
        elif roll < 0.58:
            doc[key] = text(rng, rng.randint(1, 24), wide=rng.random() < 0.35)
        elif roll < 0.68:
            doc[key] = rng.choice([True, False, None])
        elif roll < 0.82:
            doc[key] = [rng.randint(0, 999) for _ in range(rng.randint(0, 5))]
        elif depth < 3:
            doc[key] = document(rng, depth + 1)
        else:
            doc[key] = text(rng, 6)
    return doc


def context_value(rng):
    """A free-form context header. Real values carry the scheme's own punctuation."""
    return rng.choice(
        [
            "region:eu-west;tier:gold",
            "region:apac;tier:silver;retry:2",
            "batch:" + text(rng, 6) + ";lane:bulk",
            "note:" + text(rng, 8, wide=True),
            "plain-" + text(rng, 5),
        ]
    )


def legitimate(rng, key_id=None, partner=None, target=None, doc=None, ts=None, nonce=None,
               cover_drop=None, relay_headers=True):
    """Build a request the way a partner's client library and the relay actually produce it.

    cover_drop names one header the signer leaves out of its cover list. Everything else
    about the request stays well formed, which is what makes the resulting forgery a test
    of signature coverage rather than of anything else.
    """
    key_id = key_id or rng.choice(SIGNING_KEYS)
    partner = partner or rng.choice(PARTNERS)
    target = target or rng.choice(STORING_TARGETS)
    doc = document(rng) if doc is None else doc
    nonce = nonce or text(rng, 24)

    optional = {}
    if rng.random() < 0.6:
        optional["ctx"] = context_value(rng)
    if rng.random() < 0.5:
        optional["trace"] = text(rng, 16)

    headers, body = signer.sign(
        secret_for(key_id), key_id, partner, target, doc,
        ts=ts, nonce=nonce, **optional
    )

    names = [name for name in headers["x-sig-headers"].split(";") if name]
    if cover_drop is not None:
        names = [name for name in names if name != cover_drop]
        resign = True
    else:
        # Partners are free to list the headers they cover in their own order.
        resign = rng.random() < 0.5
        rng.shuffle(names)
    if resign:
        headers, body = signer.sign(
            secret_for(key_id), key_id, partner, target, doc,
            ts=ts, nonce=nonce, cover=names, **optional
        )

    if relay_headers:
        for name in rng.sample(RELAY_HEADERS, rng.randint(1, len(RELAY_HEADERS))):
            headers[name] = text(rng, 10)

    return {
        "headers": headers,
        "body": body,
        "key_id": key_id,
        "partner": partner,
        "target": target,
        "doc": doc,
        "nonce": nonce,
    }


def rng_for(name):
    """One deterministic stream per test, so failures reproduce exactly."""
    return random.Random("callback-verifier/" + name)


def reset_ledger():
    store.clear()


def env_report():
    return {
        "profile": cfg.active_profile(),
        "signing_keys": SIGNING_KEYS,
        "non_signing_keys": NON_SIGNING_KEYS,
        "max_skew_sec": MAX_SKEW_SEC,
        "app_root": os.path.realpath(APP_ROOT),
    }
