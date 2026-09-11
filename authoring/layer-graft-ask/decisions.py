"""The reference's graded decisions, as rows of integers the agent can read off the plan.

`tools/onelinecheck.py` searches these for the shortest exact rule at depth one or two. The
question is not whether a rule exists for each decision - a stated rule has one by
construction, and `guard` below is exactly that - but whether EVERY graded quantity is short.
The three that must not be are the layer a query reports, which kind of answer comes out, and
the count under a prefix: each of those is a question about what the plan did rather than
about what it says, and a copy is what takes them out of reach of the text.

Features are read from the plan as written, which is what the agent has before it builds
anything: which layers name a path, which copies cover it, how far the query counts. Labels
come from the reference.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "layer-graft-ask"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import gen  # noqa: E402
import model  # noqa: E402

GONE = -10001
LOOP = -10002


def plan_rows(text):
    """The plan as the agent reads it: layers of entry lines, then query lines."""
    layers = []
    asks = []
    for raw in text.split("\n"):
        if not raw:
            continue
        tok = raw.split(" ")
        if tok[0] == "lay":
            layers.append([])
        elif tok[0] in ("ask", "tot"):
            asks.append(tok)
        else:
            layers[-1].append(tok)
    return layers, asks


def covers(prefix, path):
    a = prefix.split(".")
    b = path.split(".")
    return len(b) >= len(a) and b[:len(a)] == a


def last_layer(layers, upto, want, path):
    """The highest layer below `upto` holding an entry of `want` that reaches `path`."""
    seen = -1
    for j, ents in enumerate(layers[:upto]):
        for tok in ents:
            if tok[0] != want:
                continue
            if want == "put" and tok[1] == path:
                seen = j
            elif want == "cut" and covers(tok[1], path):
                seen = j
            elif want == "mix" and covers(tok[2], path):
                seen = j
    return seen


def coded(run, path, stop):
    got = run.at(tuple(path.split(".")), stop)
    if got == model.GONE:
        return GONE
    if got == model.LOOP:
        return LOOP
    return got if -10000 < got < 10000 else 9999


def samples():
    out = {"guard": [], "reach": [], "kind": [], "size": []}
    for _name, text in gen.programs("decisions", 30, scale=0):
        layers, asks = plan_rows(text)
        run = model.Run(model.parse(text)[0])
        top = len(layers)

        for j, ents in enumerate(layers):
            for tok in ents:
                if "if" not in tok and "un" not in tok:
                    continue
                if tok[-3] == "if":
                    gpath, want, isun = tok[-2], int(tok[-1]), 0
                elif tok[-2] == "un":
                    gpath, want, isun = tok[-1], GONE, 1
                else:
                    continue
                row = {"atown": coded(run, gpath, j),
                       "attop": coded(run, gpath, top),
                       "want": want,
                       "isun": isun,
                       "layer": j}
                held = (row["atown"] == GONE) if isun else (row["atown"] == want)
                out["guard"].append((row, bool(held)))

        for tok in asks:
            path = tok[1]
            named = int(tok[2]) if len(tok) == 3 else top
            base = {"named": named, "top": top,
                    "lastput": last_layer(layers, named, "put", path),
                    "lastmix": last_layer(layers, named, "mix", path),
                    "lastcut": last_layer(layers, named, "cut", path),
                    "nmix": sum(1 for e in layers for t in e if t[0] == "mix")}
            if tok[0] == "tot":
                named_under = {t[1] for e in layers for t in e
                               if t[0] == "put" and covers(path, t[1])}
                row = dict(base)
                row["namedunder"] = len(named_under)
                row.pop("lastput")
                out["size"].append((row, run.size.of(
                    model.down(run.view[named], tuple(path.split("."))))))
                continue
            node = model.down(run.view[named], tuple(path.split(".")))
            got = run.at(tuple(path.split(".")), named) if (
                node is not None and node.d is not None) else model.GONE
            kind = 0 if isinstance(got, int) else (1 if got == model.GONE else 2)
            out["kind"].append((dict(base), kind))
            if isinstance(got, int):
                out["reach"].append((dict(base), node.d.h))
    return out
