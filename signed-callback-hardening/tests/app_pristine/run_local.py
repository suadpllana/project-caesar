import sys
from wsgiref.simple_server import make_server

sys.path.insert(0, "/app")

from svc import wsgi
from svc.core import cfg


def main():
    port = int(cfg.section("service").get("listen_port", 8081))
    with make_server("127.0.0.1", port, wsgi.app) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
