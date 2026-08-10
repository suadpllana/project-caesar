from ..core import cfg, jsonx, store


def apply(headers, raw):
    limits = cfg.section("ingest")
    if len(raw) > int(limits.get("max_body_bytes", 65536)):
        return 413, {"status": "too-large"}

    try:
        doc = jsonx.parse(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return 400, {"status": "bad-document"}
    if not isinstance(doc, dict):
        return 400, {"status": "bad-document"}

    seq = store.append(
        {
            "partner": headers.get("x-partner", ""),
            "target": headers.get("x-target", ""),
            "nonce": headers.get("x-nonce", ""),
            "doc": doc,
        }
    )
    return 200, {"status": "stored", "seq": seq}
