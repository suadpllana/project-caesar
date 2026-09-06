"""Write authoring/<slug>/variants/ from the reference plus one declared change each.

A variant is an alternative correct implementation: it has to reach the same
timeline by different means, and it has to score 1. Hand-copied variants drift
away from the reference silently, so every file here is generated from
solution/*.py with its change declared as a substitution that must apply.

If a variant scores 0, do not fix the variant first: ask which sentence of the
instruction separates it from the reference. If the honest answer is none, the
rule was never decided and the variant has just found it.

Usage: python3 authoring/batch-admit-reclaim/make_variants.py
"""

import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOL = os.path.join(ROOT, "tasks", "batch-admit-reclaim", "solution")
OUT = os.path.join(HERE, "variants")
POLICY = ("fit.py", "room.py", "back.py", "pick.py")

SOLVE = """#!/bin/bash
set -Eeuo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for name in fit.py room.py back.py pick.py; do
  cp "$here/$name" "/app/eng/$name"
done

python /app/run_serve.py /app/traces/steady.txt > /dev/null
"""


def source(name):
    with open(os.path.join(SOL, name)) as handle:
        return handle.read()


def edit(name, *swaps):
    text = source(name)
    for old, new in swaps:
        if old not in text:
            raise SystemExit("stale variant override in %s: %r" % (name, old[:60]))
        text = text.replace(old, new, 1)
    return text


def worklist():
    return edit("fit.py", ("""    for g in order:
        if g not in live:
            continue""", """    todo = list(order)
    while todo:
        g = todo.pop(0)
        if g not in live:
            continue"""))


def sorted_pool():
    return {
        "room.py": """def pick(pool):
    loose = [k for k in pool.blk if pool.blk[k].refs == 0]
    if not loose:
        return None
    return min(loose, key=lambda k: (pool.blk[k].touch, pool.blk[k].born))
""",
        "fit.py": edit("fit.py", ("""    for k in pool.blk:
        b = pool.blk[k]
        n = Blk(b.born)
        n.refs = b.refs
        n.touch = b.touch
        p.blk[k] = n""", """    for k in sorted(pool.blk):
        b = pool.blk[k]
        n = Blk(b.born)
        n.refs = b.refs
        n.touch = b.touch
        p.blk[k] = n""")),
    }


def counted_back():
    return {"back.py": """from eng.pool import keys


def at(pool, span, r):
    tgt = r.plen if r.have == 0 else r.have
    ks = keys(r.toks, span, tgt)
    lo, n = 0, 0
    while lo < len(ks) and pool.has(ks[lo]):
        n += 1
        lo += 1
    return n * span
"""}


def one_file():
    """All the reasoning in fit.py; the other three delegate to it."""
    body = edit("fit.py", ("from eng import back, pick", "from eng import pick"))
    body = body.replace("back.at(p, w.span, r)", "start(p, w.span, r)")
    body += """

def start(pool, span, r):
    tgt = r.plen if r.have == 0 else r.have
    n = 0
    for k in keys(r.toks, span, tgt):
        if not pool.has(k):
            break
        n += 1
    return n * span


def oldest(pool):
    best = None
    rank = None
    for k in pool.blk:
        b = pool.blk[k]
        if b.refs:
            continue
        r = (b.touch, b.born)
        if rank is None or r < rank:
            best = k
            rank = r
    return best
"""
    return {
        "fit.py": body,
        "back.py": "from eng.fit import start\n\n\ndef at(pool, span, r):\n    return start(pool, span, r)\n",
        "room.py": "def pick(pool):\n    from eng.fit import oldest\n    return oldest(pool)\n",
    }


def mirror():
    """The reference with every local name invented, to prove nothing keys on them.

    The four entry points keep their names because the frozen engine calls them
    by name; everything inside is renamed.
    """
    swaps = {
        "shadow": "mirrorpool", "drop": "letgo", "Ghost": "Stand",
        "live": "standing", "lost": "evicted", "spend": "outlay",
        "tgt": "aim", "cand": "wanting", "p": "sp", "g": "st", "r": "rq",
        "n": "clone", "k": "tagged", "b": "было",
    }
    out = {}
    for name in POLICY:
        text = source(name)
        for old, new in swaps.items():
            if new == old or not new.isascii():
                continue
            text = re.sub(r"\b%s\b" % re.escape(old), new, text)
        out[name] = text
    return out


VARIANTS = {
    "ok-worklist": {"fit.py": worklist},
    "ok-sorted-pool": sorted_pool,
    "ok-counted-back": counted_back,
    "ok-one-file": one_file,
    "ok-mirror-names": mirror,
}


def files(spec):
    out = dict((name, source(name)) for name in POLICY)
    made = spec() if callable(spec) else dict(
        (k, v() if callable(v) else v) for k, v in spec.items())
    out.update(made)
    return out


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for name in sorted(VARIANTS):
        where = os.path.join(OUT, name)
        os.makedirs(where)
        for fname, text in files(VARIANTS[name]).items():
            with open(os.path.join(where, fname), "w") as handle:
                handle.write(text)
        with open(os.path.join(where, "solve.sh"), "w") as handle:
            handle.write(SOLVE)
        os.chmod(os.path.join(where, "solve.sh"), 0o755)
        print("wrote", name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
