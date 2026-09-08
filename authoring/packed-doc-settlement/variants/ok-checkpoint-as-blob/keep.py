import json


def dump(run):
    body = {
        "par": [list(run.w), list(run.v), list(run.ema)],
        "count": run.applied,
        "open": [[k, v] for k, v in sorted(run.st.get("seen", {}).items())],
        "spent": [[k, v] for k, v in sorted(run.st.get("gen", {}).items())],
    }
    return {"blob": json.dumps(body)}


def load(run, s):
    body = json.loads(s["blob"])
    run.w, run.v, run.ema = [list(x) for x in body["par"]]
    run.applied = body["count"]
    run.st["seen"] = dict((int(k), v) for k, v in body["open"])
    run.st["gen"] = dict((int(k), v) for k, v in body["spent"])
    run.st["cnt"] = {}
