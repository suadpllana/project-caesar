"""Sandboxed executor for the agent's code.

This is the ONLY process that imports the application, and therefore the only process
that imports the agent's /app/svc/auth/verify.py. tests/test.sh launches it unprivileged
(setpriv to nobody, --no-new-privs) with /logs and /tests unreadable to that user, so
nothing the agent submits runs in the grading process or can touch the reward file.

It speaks one JSON object per line on stdin and answers one JSON object per line on the
protocol stream. Before importing anything from /app, file descriptor 1 is duplicated
away and replaced by stderr, so output printed by agent code cannot be mistaken for a
protocol reply.
"""

import base64
import io
import json
import os
import sys

APP_ROOT = "/app"

_protocol = os.fdopen(os.dup(1), "w", encoding="utf-8")
os.dup2(2, 1)

sys.path.insert(0, APP_ROOT)


def build_environ(request):
    body = base64.b64decode(request["body"])
    environ = {
        "REQUEST_METHOD": request.get("method", "POST"),
        "PATH_INFO": request.get("path", "/v1/callback"),
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }
    for name, value in request["headers"].items():
        environ["HTTP_" + name.upper().replace("-", "_")] = value
    return environ


def deliver(wsgi, store, request):
    before = len(store.entries())
    captured = {}

    def start_response(status, response_headers):
        captured["status"] = status

    try:
        chunks = wsgi.app(build_environ(request), start_response)
        payload = json.loads(b"".join(chunks).decode("utf-8"))
        status = int(captured["status"].split()[0])
    except Exception as exc:  # an unhandled error is a failure, not a rejection
        return {"status": 500, "payload": {"status": "exception", "detail": repr(exc)},
                "records": store.entries()[before:]}
    return {"status": status, "payload": payload, "records": store.entries()[before:]}


def main():
    from svc import wsgi
    from svc.core import store

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            op = request.get("op")
            if op == "ping":
                reply = {"ok": True, "pid": os.getpid(), "uid": os.getuid()}
            elif op == "reset":
                store.clear()
                reply = {"ok": True}
            elif op == "deliver":
                reply = dict(deliver(wsgi, store, request), ok=True)
            else:
                reply = {"ok": False, "error": "unknown op %r" % (op,)}
        except Exception as exc:
            reply = {"ok": False, "error": repr(exc)}
        _protocol.write(json.dumps(reply) + "\n")
        _protocol.flush()


if __name__ == "__main__":
    main()
