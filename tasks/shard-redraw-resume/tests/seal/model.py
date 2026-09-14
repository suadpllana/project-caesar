"""The sealed model: what a program is supposed to print.

Written against the frozen contract on its own, in a shape the reference deliberately does not
share. The reference carries the epoch in an object with slots and settles the window through a
separate span call; this is one flat driver over a dict that walks the order inline. It also
takes the slow road on purpose wherever the road does not change the answer: it tests whether a
sample has already been fed by asking every order the epoch has used, in the order they were
used, and it re-derives the scan head from the ledger each time instead of carrying it. The two
agree on every graded program, which is what makes the agreement evidence about the contract
rather than about one way of writing it.

The permutation is frozen, not editable, and is imported from the verifier's own pristine copy
of the tree, so nothing the agent submits can move it. Its inverse is not shipped anywhere and
is re-derived here, because the contract is about which samples an epoch has already handed out
and that question is asked of a sample, not of a position.
"""

import os
import sys

sys.path.insert(0, os.environ.get("SRR_PRISTINE", "/tests/pristine"))

from rig import shuf  # noqa: E402

HEAD = ("rows", "seed", "rank", "micro", "accum", "ckpt", "grow", "scale", "epochs")

START = {"rows": 1, "seed": 0, "rank": 1, "micro": 1, "accum": 1,
         "ckpt": 1, "grow": 1, "scale": 0, "epochs": 1}


def _back(cfg, epoch, rank, x):
    """Where sample x stands in the order for this epoch and this rank count."""
    half, mask, salt = shuf._setup(cfg["seed"], epoch, rank, cfg["rows"])
    y = x
    while True:
        lo = y & mask
        hi = y >> half
        for rnd in (3, 2, 1, 0):
            hi, lo = lo ^ (shuf._mix(salt + (hi << 6) + rnd) & mask), hi
        y = (hi << half) | lo
        if y < cfg["rows"]:
            return y


def _already(cfg, st, x):
    """Has this epoch handed x out already, under any order it has run on?"""
    for rank, head in st["seen"].items():
        if head and _back(cfg, st["epoch"], rank, x) < head:
            return True
    return False


def _take(cfg, st, wide):
    """The next `wide` samples of the current order this epoch has not handed out yet."""
    rank = st["rank"]
    at = st["seen"].get(rank, 0)
    got = []
    while len(got) < wide:
        x = shuf.at(cfg["seed"], st["epoch"], rank, cfg["rows"], at)
        at += 1
        if not _already(cfg, st, x):
            got.append(x)
    st["seen"][rank] = at
    st["fed"] += wide
    return got


def _lanes(cfg, st, got):
    """One window dealt out: chunk c of `micro` samples goes to rank c % rank."""
    rank, micro = st["rank"], cfg["micro"]
    lanes = [[] for _ in range(rank)]
    for c in range(len(got) // micro):
        lanes[c % rank].extend(got[c * micro:(c + 1) * micro])
    return lanes


def _walk(cfg, st, out, nf, left):
    """Attempt up to `left` steps. Rolling an epoch costs nothing out of that budget."""
    while left > 0 and st["epoch"] < cfg["epochs"]:
        wide = st["rank"] * cfg["micro"] * cfg["accum"]
        if cfg["rows"] - st["fed"] < wide:
            st["epoch"] += 1
            st["seen"] = {}
            st["fed"] = 0
            out.append("roll %d" % st["epoch"])
            continue
        left -= 1
        lanes = _lanes(cfg, st, _take(cfg, st, wide))
        for r, ids in enumerate(lanes):
            out.append("feed %d %s" % (r, " ".join(str(i) for i in ids)))
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
            st["saved"] = (st["epoch"], dict(st["seen"]), st["fed"],
                           st["done"], st["sc"], st["gt"])
            out.append("save %d %d %d" % (st["done"], st["epoch"], st["fed"]))


def _fresh(cfg):
    return {"epoch": 0, "seen": {}, "fed": 0, "done": 0, "sc": cfg["scale"], "gt": 0,
            "rank": cfg["rank"], "saved": None}


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
            st = _fresh(cfg)
        if name == "run":
            _walk(cfg, st, out, nf, int(tok[1]))
        elif name == "kill":
            if st["saved"] is None:
                keep, rank = st["saved"], st["rank"]
                st.update(_fresh(cfg))
                st["saved"], st["rank"] = keep, rank
            else:
                (st["epoch"], seen, st["fed"],
                 st["done"], st["sc"], st["gt"]) = st["saved"]
                st["seen"] = dict(seen)
            out.append("kill %d %d" % (st["epoch"], st["fed"]))
        elif name == "back":
            st["rank"] = int(tok[1])
            out.append("back %d" % st["rank"])
        else:
            raise ValueError(name)
    out.append("halt %d" % (0 if st is None else st["done"]))
    return out
