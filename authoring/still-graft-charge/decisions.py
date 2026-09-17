"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at that moment: how many cells a head holds and what they add
up to, what the line holds once its own stills are counted, what the shipped reference count
says is unshared, the cap, what a put adds, how much of its range is already held, how many
stills the line owns, how many lines exist, and whether this line was grafted. The two
arithmetics a first plan reaches for are offered ready-made - the charge plus what the put adds,
and the head plus what the put adds - because refusing to offer them would only hide a short
rule that a solver would write.

Nothing per-block is offered beyond what a reference count exposes, because which lines hold a
block is the derivation and the derivation is the task.

The verdict to want is that at least one graded quantity has no short rule. Two should not: the
charge itself, because it is a question about how many lines hold each block rather than how
many places do, and what a drop releases, because it is the same question asked of the blocks a
still was holding.

    python3 tools/onelinecheck.py still-graft-charge
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import brute  # noqa: E402
import gen  # noqa: E402

ROWS = {"put-full": [], "ask-charge": [], "drop-free": []}


def places(store, block):
    """How many places hold a block: a head counts once, and so does each still."""
    n = 0
    for line in store.lines.values():
        n += sum(1 for b in line.head.values() if b is block)
    for still in store.stills.values():
        n += sum(1 for b in still.held.values() if b is block)
    return n


def view(store, name):
    """What the shipped tree would show about one line."""
    line = store.lines[name]
    mine = {}
    for b in line.head.values():
        mine[id(b)] = b
    for s in line.stills:
        for b in store.stills[s].held.values():
            mine[id(b)] = b
    heads = {}
    for other, one in store.lines.items():
        if other == name:
            continue
        for b in one.head.values():
            heads[id(b)] = b
    return {
        "cells": len(line.head),
        "headsize": sum(b.size for b in line.head.values()),
        "mine": sum(b.size for b in mine.values()),
        "rc1": sum(b.size for b in line.head.values() if places(store, b) == 1),
        "unshared": sum(b.size for b in mine.values() if id(b) not in heads),
        "stills": len(line.stills),
        "lines": len(store.lines),
        "grafted": int(line.origin is not None),
    }


def watch(store):
    """Wrap the three ops that print a graded number, and record what was visible."""
    put, ask, drop = store.op_put, store.op_ask, store.op_drop

    def op_put(name, lo, hi, size):
        line = store.lines[name]
        if line.cap is None:
            return put(name, lo, hi, size)
        row = view(store, name)
        add = (hi - lo + 1) * size
        row.update({
            "add": add,
            "cap": line.cap,
            "over": sum(1 for c in range(lo, hi + 1) if c in line.head),
            "after_charge": row["rc1"] + add,
            "after_head": row["headsize"] + add,
        })
        before = len(store.out)
        put(name, lo, hi, size)
        said = store.out[before:]
        ROWS["put-full"].append((row, bool(said and said[0].startswith("full"))))

    def op_ask(name):
        row = view(store, name)
        before = len(store.out)
        ask(name)
        ROWS["ask-charge"].append((row, int(store.out[before].split()[2])))

    def op_drop(still):
        rec = store.stills.get(still)
        if rec is None:
            return drop(still)
        held = list(rec.held.values())
        others = {}
        for name, one in store.stills.items():
            if name == still:
                continue
            for b in one.held.values():
                others[id(b)] = b
        heads = {}
        for one in store.lines.values():
            for b in one.head.values():
                heads[id(b)] = b
        row = view(store, rec.owner)
        row.update({
            "stillsize": sum(b.size for b in held),
            "no_other_still": sum(b.size for b in held if id(b) not in others),
            "no_head": sum(b.size for b in held if id(b) not in heads),
            "places1": sum(b.size for b in held if places(store, b) == 1),
        })
        before = len(store.out)
        drop(still)
        said = store.out[before:]
        if said and said[0].startswith("free"):
            ROWS["drop-free"].append((row, int(said[0].split()[2])))

    store.op_put, store.op_ask, store.op_drop = op_put, op_ask, op_drop


def samples():
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(6):
            lines = gen.one(fam, "decide/%s-%d" % (fam, i))
            store = brute.Store()
            watch(store)
            for line in lines:
                brute.ex(store, tuple(line.split()))
    return ROWS
