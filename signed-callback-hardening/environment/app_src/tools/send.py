import io
import json
import sys

sys.path.insert(0, "/app")

from sdk import signer
from svc import wsgi
from svc.auth import keys
from svc.core import store


def call(headers, body, method="POST", path="/v1/callback"):
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
    return captured.get("status", ""), json.loads(b"".join(chunks).decode("utf-8"))


def main(argv):
    key_id = argv[1] if len(argv) > 1 else "k-beta-1"
    partner = argv[2] if len(argv) > 2 else "pt-beta"
    target = argv[3] if len(argv) > 3 else "settle"
    doc = json.loads(argv[4]) if len(argv) > 4 else {"ref": "demo-1", "amount": 125}

    entry = keys.lookup(key_id)
    if entry is None:
        print("no such key: " + key_id)
        return 2

    headers, body = signer.sign(entry["secret"], key_id, partner, target, doc)
    status, payload = call(headers, body)
    print(status)
    print(json.dumps(payload))
    print(json.dumps(store.entries()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
