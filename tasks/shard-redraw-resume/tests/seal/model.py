"""The sealed model: what a program is supposed to print.

Written against the frozen contract on its own, in a shape the reference deliberately does not
share. The reference splits the run across six modules and carries the leg in an object with
slots; this is one flat driver over a dict, it deals a window by walking the window's positions
once and posting each micro-batch to `chunk % rank` instead of indexing rank by rank, and it
tests the epoch edge inside the step loop rather than through a separate span call. The two
agree on every graded program, which is what makes the agreement evidence about the contract
rather than about one way of writing it.

The permutation itself is not re-derived here. It is frozen, not editable, and is imported from
the verifier's own pristine copy of the tree, so nothing the agent submits can move it.
"""

import os
import sys

sys.path.insert(0, os.environ.get("SRR_PRISTINE", "/tests/pristine"))

from rig import shuf  # noqa: E402

HEAD = ("rows", "seed", "rank", "micro", "accum", "ckpt", "grow", "scale", "epochs")

START = {"rows": 1, "seed": 0, "rank": 1, "micro": 1, "accum": 1,
         "ckpt": 1, "grow": 1, "scale": 0, "epochs": 1}


def _lanes(cfg, st, start, wide):
    """One window dealt out: chunk c of `micro` positions goes to rank c % rank."""
    rank, micro = st["rank"], cfg["micro"]
    lanes = [[] for _ in range(rank)]
    if rank <= 0 or micro <= 0:
        return lanes
    for c in range(wide // micro):
        at = start + c * micro
        lanes[c % rank].extend(
            shuf.at(cfg["seed"], st["epoch"], rank, cfg["rows"], at + m)
            for m in range(micro))
    return lanes


def _walk(cfg, st, out, nf, left):
    """Attempt up to `left` steps. Rolling an epoch costs nothing out of that budget."""
    while left > 0 and st["epoch"] < cfg["epochs"]:
        wide = st["rank"] * cfg["micro"] * cfg["accum"]
        if cfg["rows"] - st["seen"] < wide:
            st["epoch"] += 1
            st["seen"] = 0
            out.append("roll %d" % st["epoch"])
            continue
        left -= 1
        start = st["seen"]
        lanes = _lanes(cfg, st, start, wide)
        for r, ids in enumerate(lanes):
            out.append("feed %d %s" % (r, " ".join(str(i) for i in ids)))
        st["seen"] = start + wide
        if any(i in nf for ids in lanes for i in ids):
            st["sc"] = st["sc"] - 1 if st["sc"] > 0 else st["sc"]
            st["gt"] = 0
            out.append("skip %d" % st["sc"])
            continue
        st["done"] += 1
        st["gt"] += 1
        if st["gt"] >= cfg["grow"]:
            st["sc"] += 1
            st["gt"] = 0
        out.append("step %d %d" % (st["done"], st["sc"]))
        if cfg["ckpt"] > 0 and st["done"] % cfg["ckpt"] == 0:
            st["saved"] = (st["epoch"], st["seen"], st["done"], st["sc"], st["gt"])
            out.append("save %d %d %d" % (st["done"], st["epoch"], st["seen"]))


def expect(lines):
    """Replay a program and return the trace it should print, line for line."""
    cfg = dict(START)
    nf = set()
    out = []
    st = None
    for line in lines:
        tok = line.split()
        if not tok:
            continue
        name = tok[0]
        if name in HEAD:
            cfg[name] = int(tok[1])
            continue
        if name == "nf":
            nf.add(int(tok[1]))
            continue
        if st is None:
            st = {"epoch": 0, "seen": 0, "done": 0, "sc": cfg["scale"], "gt": 0,
                  "rank": cfg["rank"], "saved": None}
        if name == "run":
            _walk(cfg, st, out, nf, int(tok[1]))
        elif name == "kill":
            if st["saved"] is None:
                st["epoch"], st["seen"], st["done"] = 0, 0, 0
                st["sc"], st["gt"] = cfg["scale"], 0
            else:
                (st["epoch"], st["seen"], st["done"],
                 st["sc"], st["gt"]) = st["saved"]
            out.append("kill %d %d" % (st["epoch"], st["seen"]))
        elif name == "back":
            st["rank"] = int(tok[1])
            out.append("back %d" % st["rank"])
        else:
            raise ValueError(name)
    out.append("halt %d" % (0 if st is None else st["done"]))
    return out
