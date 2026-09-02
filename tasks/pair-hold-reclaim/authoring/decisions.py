"""The graded decisions as rows of features an agent can read at the moment it decides.

tools/onelinecheck.py searches these for the shortest exact rule over the fields the
environment already exposes. A graded decision a two-term rule reproduces is an easiness
rejection waiting to happen: a frontier model writes two correct terms cold, whatever is
hidden from it.

Three decisions are exported, one per question the pass has to answer:

  keep      for each cell alive at the start of a pass, whether the pass lets it go
  clean     for each cell with a pending cleanup, whether this round is the round it
            runs in
  fade      for each watch, whether this pass empties it

The features are the ones a submission can read off the store without doing the work:
how many links lead out, how many lead in, whether a name is bound straight to it,
whether it is a key or a value of either entry table, whether a cleanup is pending, its
age, and the sizes of the tables. Reachability itself is not a feature, because
computing it is the task.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402


def _features(m, i):
    ins = sum(1 for c in m.seq for j in m.link[c] if j == i)
    return {
        "outs": len(m.link.get(i, [])),
        "ins": ins,
        "named": int(any(v == i for v in m.root.values())),
        "onekey": sum(1 for k, _ in m.one if k == i),
        "oneval": sum(1 for _, v in m.one if v == i),
        "twokey": sum(1 for a, b, _ in m.two if i in (a, b)),
        "twoval": sum(1 for _, _, v in m.two if v == i),
        "pend": int(m.pending(i)),
        "armed": int(i in m.act),
        "age": m.seq.index(i),
        "cells": len(m.seq),
        "names": len(m.root),
    }


def samples():
    """Replay every stream through the model, snapshotting each decision it makes."""
    out = {"keep": [], "clean": [], "fade": []}
    streams = scen.cases() + gen.build("decisions", 120)
    for _name, text in streams:
        m = oracle.Model()
        ops = oracle.read(text)
        for op in ops:
            if op[0] != "pass":
                _apply(m, op)
                continue
            before = list(m.seq)
            shots = {i: _features(m, i) for i in before}
            watches = {nm: (m.wtgt[nm], m.wkind[nm], m.woff[nm]) for nm in m.wname}
            pend = [i for i in before if m.pending(i)]
            m.sweep()
            for i in before:
                out["keep"].append((shots[i], int(i not in m.seq)))
            for i in pend:
                out["clean"].append((shots[i], int(i in m.ran)))
            for nm, (tgt, _kd, was) in watches.items():
                if not was and tgt in shots:
                    out["fade"].append((shots[tgt], int(m.woff[nm])))
    return out


def _apply(m, op):
    h = op[0]
    if h == "new":
        m.mk(op[1])
    elif h == "edge":
        m.edge(op[1], op[2])
    elif h == "cut":
        m.cut(op[1], op[2])
    elif h == "pair":
        m.one_add(op[1], op[2])
    elif h == "both":
        m.two_add(op[1], op[2], op[3])
    elif h == "bind":
        m.bind(op[1], op[2])
    elif h == "unbind":
        m.unbind(op[1])
    elif h == "watch":
        m.see(op[1], op[2], op[3])
    elif h == "arm":
        m.arm(op[1], op[2])
    elif h == "show":
        m.look(op[1])


if __name__ == "__main__":
    for k, v in sorted(samples().items()):
        yes = sum(1 for _, lab in v if lab)
        print("%-6s %5d samples, %d positive" % (k, len(v), yes))
