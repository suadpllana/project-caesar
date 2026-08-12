import json
import os


def base(appdir):
    with open(os.path.join(appdir, "conf", "train.json")) as fh:
        return json.load(fh)


def merge(cfg, over):
    for k, v in (over or {}).items():
        if k == "sched":
            for a, b in v.items():
                cfg["sched"][a] = b
        else:
            cfg[k] = v
    return cfg


def corpus(path):
    with open(path) as fh:
        return int(json.load(fh)["dseed"])
