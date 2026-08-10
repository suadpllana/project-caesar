"""Shared machinery for the verifier.

Everything here drives the *composed* service: the pristine application tree that this
image bakes at /app, with the agent's /app/svc/auth/verify.py dropped in on top by the
harness. Requests go through /app/svc/wsgi.py exactly as they would over the wire, so a
test observes what the whole pipeline did, not what one function returned.

The application runs in a separate unprivileged process (see tests/worker.py), never in
this one. Agent-supplied code therefore cannot reach pytest, the test files, or
/logs/verifier: killing or hanging its own process shows up here as a failed test, and
the reward is graded afterwards from the CTRF report by tests/grade.py, not from an exit
status this process could produce without running anything.
"""

import atexit
import base64
import json
import os
import random
import select
import shutil
import subprocess
import sys

APP_ROOT = "/app"
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# Only modules the agent cannot supply are imported here. The single file collected from
# the agent is /app/svc/auth/verify.py, which nothing below pulls in: svc/__init__.py and
# svc/auth/__init__.py are empty, and none of these modules import the verifier. Anything
# that reaches the agent's code goes through the sandboxed worker instead.
from sdk import signer  # noqa: E402
from svc.auth import keys  # noqa: E402
from svc.core import cfg  # noqa: E402

WORKER_TIMEOUT_SEC = 60
UNPRIVILEGED_UID = "65534"


class WorkerError(AssertionError):
    """Raised when the sandboxed application process misbehaves or goes away."""


class Worker:
    """A separate, unprivileged process that owns the application and its state.

    One worker serves the whole session, because the verifier under test keeps state
    across requests. If it dies, exits early, or stops answering, every remaining test
    fails: there is no restart, and a silent exit cannot be mistaken for success.
    """

    def __init__(self):
        self.proc = subprocess.Popen(
            self.command(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=self.child_env(),
            close_fds=True,
        )
        atexit.register(self.close)

    @staticmethod
    def script_path():
        for candidate in ("/run/worker.py", os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker.py")):
            if os.path.isfile(candidate):
                return candidate
        raise WorkerError("the sandboxed worker script is missing")

    @classmethod
    def command(cls):
        base = [sys.executable, "-u", cls.script_path()]
        setpriv = shutil.which("setpriv")
        if os.geteuid() == 0 and setpriv:
            return [setpriv, "--reuid", UNPRIVILEGED_UID, "--regid", UNPRIVILEGED_UID,
                    "--clear-groups", "--no-new-privs", "--"] + base
        return base

    @staticmethod
    def child_env():
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "LANG", "LC_ALL", "SVC_PROFILE")}
        env["HOME"] = "/tmp"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return env

    def ask(self, message):
        if self.proc.poll() is not None:
            raise WorkerError(
                "the application process exited with status %s before answering; agent "
                "code that terminates the process is a failure, not a pass"
                % self.proc.returncode
            )
        try:
            self.proc.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError) as exc:
            raise WorkerError("the application process stopped accepting requests (%r)" % exc)

        ready, _, _ = select.select([self.proc.stdout], [], [], WORKER_TIMEOUT_SEC)
        if not ready:
            raise WorkerError("the application process did not answer within %d seconds"
                              % WORKER_TIMEOUT_SEC)
        line = self.proc.stdout.readline()
        if not line:
            raise WorkerError(
                "the application process closed its output without answering (exit status "
                "%s); this is what a verify.py that kills the process looks like"
                % self.proc.poll()
            )
        reply = json.loads(line.decode("utf-8"))
        if not reply.get("ok"):
            raise WorkerError("the application process reported an error: %s"
                              % reply.get("error"))
        return reply

    def close(self):
        if self.proc.poll() is None:
            try:
                self.proc.stdin.close()
            except Exception:
                pass
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()


_worker = None


def worker():
    global _worker
    if _worker is None:
        _worker = Worker()
    return _worker

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


def deliver(headers, body, method="POST", path="/v1/callback"):
    """Send a request through the sandboxed application and report what it did.

    Returns (status_code, payload, new_records). new_records is what the ingest handler
    appended to the ledger during this request, which is the observable effect an
    attacker is trying to produce.
    """
    reply = worker().ask({
        "op": "deliver",
        "method": method,
        "path": path,
        "headers": headers,
        "body": base64.b64encode(bytes(body)).decode("ascii"),
    })
    return reply["status"], reply["payload"], reply["records"]


def call(headers, body, method="POST", path="/v1/callback"):
    status, payload, _ = deliver(headers, body, method=method, path=path)
    return status, payload


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
    worker().ask({"op": "reset"})


def env_report():
    reply = worker().ask({"op": "ping"})
    return {
        "profile": cfg.active_profile(),
        "signing_keys": SIGNING_KEYS,
        "non_signing_keys": NON_SIGNING_KEYS,
        "max_skew_sec": MAX_SKEW_SEC,
        "app_root": os.path.realpath(APP_ROOT),
        "worker_uid": reply.get("uid"),
        "grader_imported_app": [name for name in sys.modules if name.startswith("svc.wsgi")],
    }
