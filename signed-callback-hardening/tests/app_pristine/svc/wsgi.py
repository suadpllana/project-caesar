import io
import json

from .auth import verify
from .handlers import routing

MAX_BODY_BYTES = 1 << 20

_labels = {
    200: "200 OK",
    400: "400 Bad Request",
    401: "401 Unauthorized",
    404: "404 Not Found",
    413: "413 Payload Too Large",
}


def collect_headers(environ):
    out = {}
    for key, value in environ.items():
        if key.startswith("HTTP_") and isinstance(value, str):
            out[key[5:].lower().replace("_", "-")] = value
    return out


def collect_body(environ):
    try:
        size = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        return b""
    if size <= 0 or size > MAX_BODY_BYTES:
        return b""
    stream = environ.get("wsgi.input") or io.BytesIO(b"")
    return stream.read(size)


def reply(start_response, code, payload):
    body = json.dumps(payload).encode("utf-8")
    start_response(
        _labels.get(code, "500 Internal Server Error"),
        [("Content-Type", "application/json"), ("Content-Length", str(len(body)))],
    )
    return [body]


def app(environ, start_response):
    headers = collect_headers(environ)
    for name, value in headers.items():
        if any(ord(char) < 32 for char in value):
            return reply(start_response, 400, {"status": "bad-header", "name": name})

    request = {
        "method": environ.get("REQUEST_METHOD", "GET"),
        "path": environ.get("PATH_INFO", "/"),
        "headers": headers,
        "body": collect_body(environ),
    }

    accepted, reason = verify.check(request)
    if not accepted:
        return reply(start_response, 401, {"status": "rejected", "reason": reason})

    code, payload = routing.dispatch(request["headers"], request["body"])
    return reply(start_response, code, payload)
