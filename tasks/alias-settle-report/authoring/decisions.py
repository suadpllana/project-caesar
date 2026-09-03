"""The graded decisions, as rows of integer features an agent could read at the
moment it makes them, plus the label the reference chose.

tools/onelinecheck.py searches these for the shortest exact rule. The features
are deliberately generous: everything cheap that the exposed state offers,
including the reach a solver computes when it has understood that a still-open
tag can weld and has NOT understood that a declared difference bounds which
welds are possible. If a two-term rule over that lot reproduces the filing
decision, the answer is short and the task is an easiness rejection waiting to
happen.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
TREE = os.path.join(TASK, "environment", "app_src")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, TREE)

import cases
import gen

BIG = 9999


def _policy():
    import importlib
    box = {}
    for name in ("rch", "hold", "card", "seq"):
        spec = importlib.util.spec_from_file_location(
            "ref_" + name, os.path.join(TASK, "solution", name + ".py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["bind." + name] = mod
        spec.loader.exec_module(mod)
        box[name] = mod
    return box


def _hops(bk, c):
    cells = bk.cells()
    out = set()
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        if pool & set(cells[c]):
            for i in cells:
                if i != c and pool & set(cells[i]):
                    out.add(i)
    return out


def _loose(bk, c):
    cells = bk.cells()
    near = dict((i, set()) for i in cells)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        hit = [i for i in cells if pool & set(cells[i])]
        for i in hit:
            near[i].update(j for j in hit if j != i)
    seen = {c}
    work = [c]
    while work:
        i = work.pop()
        for j in near[i] - seen:
            seen.add(j)
            work.append(j)
    return seen - {c}


def _feat(bk, c, card):
    cells = bk.cells()
    keys = cells[c]
    a = card.auth(bk, c)
    hop = _hops(bk, c)
    loose = _loose(bk, c)
    pend_here = pend_loose = 0
    here = set(keys)
    wide = set(keys)
    for x in loose:
        wide.update(cells[x])
    for n in bk.open_runs():
        for k in bk.unsent(n):
            if a is not None and (n, k) < a:
                pend_here += k in here
                pend_loose += k in wide
    return {
        "low": keys[0],
        "size": len(keys),
        "hasscore": 1 if a is not None else 0,
        "cells": len(cells),
        "opentags": len(bk.open_tags()),
        "openruns": len(bk.open_runs()),
        "touching": len(hop),
        "hoplow": min([cells[i][0] for i in hop], default=BIG),
        "reachwide": len(loose),
        "reachlow": min([cells[i][0] for i in loose], default=BIG),
        "bars": len(bk.bars),
        "pendhere": pend_here,
        "pendreach": pend_loose,
    }


def _walk(text, card, hold, out_file, out_front, out_score):
    from bind.bk import Book
    from bind.rd import parse
    sp = parse(text)
    bk = Book(sp)
    for kind, who, a, b in sp.script:
        if kind == "post":
            bk.post[(who, a)] = b
        elif kind == "tie":
            bk.weld(a, b)
        elif kind == "bar":
            bk.bars.add((min(a, b), max(a, b)))
        elif kind == "shut":
            bk.live.discard(who)
        for w in bk.watch:
            if w in bk.filed:
                continue
            c = bk.find(w)
            row = _feat(bk, c, card)
            label = bool(hold.firm(bk, c))
            out_file.append((row, label))
            if label:
                rep, sc = card.card(bk, c)
                out_front.append((dict(row), rep))
                out_score.append((dict(row), sc))
        for w in list(bk.watch):
            if w not in bk.filed and hold.firm(bk, bk.find(w)):
                bk.filed.add(w)


def samples():
    box = _policy()
    card, hold = box["card"], box["hold"]
    files, fronts, scores = [], [], []
    texts = [cases.SETS[n] for n in sorted(cases.SETS)]
    texts += [gen.one("dec:%d" % i) for i in range(60)]
    for text in texts:
        _walk(text, card, hold, files, fronts, scores)
    return {
        "file-now": files,
        "row-front": fronts,
        "row-score": scores,
    }
