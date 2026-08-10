from . import health, ingest

_routes = {
    "settle": ingest.apply,
    "notify": ingest.apply,
    "status": health.probe,
}


def dispatch(headers, raw):
    handler = _routes.get(headers.get("x-target", ""))
    if handler is None:
        return 404, {"status": "unknown-target"}
    return handler(headers, raw)
