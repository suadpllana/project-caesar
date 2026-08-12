"""Drives the rebuilt trainer through every scenario and dumps what the service observed.

This process is the trainer's supervisor, and it is not a place agent code runs.  It
imports the supervisor half of the tree - train/drv.py and core/svc.py - from the sealed
copy under SUPDIR, never from the tree the agent's files were overlaid onto, and it never
imports build.py or anything build.py reaches.  Every scenario's trainer runs as a child
process it spawns: unprivileged, in its own session, holding no state this process cannot
see.  A kill in a scenario kills that process outright and the next load starts another
one, so the only thing that crosses a kill is the vector the checkpoint channel accepted.

The service the children talk to lives here.  It owns the corpus, which is generated from
a seed that never leaves this process, so a child cannot produce a sample's tokens without
asking for them; it owns the gradient and optimiser kernels; and it owns the counters,
which are therefore measurements of what the service was actually asked to do rather than
numbers a child reported about itself.  The record of microbatches and updates is written
here too, from those same requests: a child that announces a microbatch of three rows when
the service handed it two gets an error rather than a trace entry.

The result lands in a work file this process owns.  Nothing the children run can write it.
Grading happens afterwards, as root, in pytest, against /tests/gt.json.
"""

import json
import os
import subprocess
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
SUP = os.environ.get("SUPDIR", "/pristine")
CORPUS = os.environ.get("CORPUS", os.path.join(HERE, "corpus.json"))
CONF = os.environ.get("CONF_JSON", os.path.join(HERE, "train.json"))

sys.path.insert(0, HERE)
sys.path.insert(0, SUP)

import scen  # noqa: E402
from core import conf  # noqa: E402
from train import drv  # noqa: E402


def drop_privileges():
    """The credentials every trainer process is started under.

    setuid and setgid to LIFE_UID with no supplementary groups, applied by the interpreter
    in the child between the fork and the exec.  The supervisor stays root because it has
    to be able to reap the trainer's uid; nothing the agent wrote runs in it.
    """
    return drv.creds()


def probe():
    """Prove the drop before grading anything on top of it.

    One child, started under exactly those credentials, asked what uid it came up as. A
    platform that cannot answer 1002 is a platform this verifier will not grade on, and
    saying so once is worth more than every scenario reporting that the trainer went away.
    """
    out = {"uid": os.geteuid(), "drop": "not requested"}
    cred = drop_privileges()
    if not cred:
        return out
    out["drop"] = "failed"
    try:
        p = subprocess.run([sys.executable, "-c", "import os;print(os.getuid())"],
                           capture_output=True, text=True, timeout=120, **cred)
    except Exception as exc:
        out["why"] = "%s: %s" % (type(exc).__name__, exc)
        return out
    got = (p.stdout or "").strip()
    if got == str(cred["user"]):
        out["drop"] = "ok"
        out["uid"] = cred["user"]
    else:
        out["why"] = "a child came up as %r, expected %r" % (got, str(cred["user"]))
    return out


def main(dest):
    ds = conf.corpus(CORPUS)
    with open(CONF) as fh:
        base = json.load(fh)

    out = {"reports": {}, "errors": {}, "env": probe()}
    with open(dest, "w") as f:
        json.dump(out, f)
    for sc in scen.SCENARIOS:
        name = sc["name"]
        cfg = conf.merge(json.loads(json.dumps(base)), sc.get("over") or {})
        try:
            out["reports"][name] = drv.play(cfg, sc["ops"], ds)
        except Exception:
            out["errors"][name] = traceback.format_exc()[-2000:]
        with open(dest, "w") as f:
            json.dump(out, f)
    return 0


if __name__ == "__main__":
    target = sys.argv[1]
    try:
        sys.exit(main(target))
    except Exception:
        with open(target, "w") as fh:
            json.dump({"reports": {}, "errors": {"fatal": traceback.format_exc()[-2000:]},
                       "env": {"drop": "unknown"}}, fh)
        sys.exit(1)
