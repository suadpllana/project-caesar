"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at that moment: the proposal's base and the head, the slab's
one stamp as the shipped engine records it, how many keys it holds and how many of them lie
inside the range, how many runs it has, whether its first and last key fall inside, and how many
slabs the window holds. Nothing per-key is offered, because per-key is the derivation and the
derivation is the task.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
which slabs a fold takes, because the answer is a property of every key in a slab and the tree
records one number per slab, and whether a fold undoes the attempt, because that is the same
question asked of a slab the window may only partly hold.

    python3 tools/onelinecheck.py slab-fold-scope
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402

ROWS = {"fold-reach": [], "fold-trip": [], "push-void": []}


def _look(live, take, b, lo, hi, base, head):
    """What the shipped tree would show about each slab the window holds."""
    i, j = live.window(b, lo, hi)
    seen = {}
    for t in range(i, j):
        d = b.ds[t]
        s = b.ss[t]
        wide = min(b.es[t], hi) - max(b.ks[t], lo) + 1
        e = seen.get(d)
        if e is None:
            seen[d] = [wide, s, s, 1, b.ks[t], b.es[t]]
        else:
            e[0] += wide
            e[1] = min(e[1], s)
            e[2] = max(e[2], s)
            e[3] += 1
            e[4] = min(e[4], b.ks[t])
            e[5] = max(e[5], b.es[t])
    out = {}
    for d, e in seen.items():
        out[d] = {
            "base": base, "head": head, "gap": head - base,
            "keys": b.sn[d], "keys_in": e[0], "runs": e[3],
            "first_in": int(e[4] >= lo), "last_in": int(e[5] <= hi),
            "born": e[1], "pack": len(seen),
        }
    return out


def samples():
    here = lab.tree(lab.TASK / "solution")
    sys.path.insert(0, str(here))
    import ops
    from tab import live, push, store, take

    plain = take.part
    drive = push.run

    def watched(tab, base, buck, lo, hi, jr):
        b = live.hold(tab, buck)
        view = _look(live, take, b, lo, hi, base, tab.head)
        try:
            got = plain(tab, base, buck, lo, hi, jr)
        except take.Again:
            ROWS["fold-trip"].append((_part_row(view), True))
            raise
        ROWS["fold-trip"].append((_part_row(view), False))
        after = set(b.ds)
        for d, row in view.items():
            ROWS["fold-reach"].append((row, got and d not in after))
        return got

    def watched_push(tab, prop):
        kinds = [p[0] for p in prop.parts]
        before = len(tab.out)
        row = {
            "parts": len(kinds), "puts": kinds.count("put"), "cuts": kinds.count("cut"),
            "folds": kinds.count("fold"), "base": prop.base, "head": tab.head,
            "gap": tab.head - prop.base,
        }
        drive(tab, prop)
        line = tab.out[before] if len(tab.out) > before else ""
        ROWS["push-void"].append((row, line.startswith("void")))

    take.part = watched
    push.run = watched_push

    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(8):
            lines = gen.one(fam, "decide/%s-%d" % (fam, i))
            tab = store.Tab()
            for line in lines:
                ops.ex(tab, tuple(line.split()))
    return ROWS


def _part_row(view):
    if not view:
        return {"pack": 0, "inside": 0, "base": 0, "head": 0, "gap": 0,
                "oldest": 0, "newest": 0, "runs": 0}
    rows = list(view.values())
    inside = [r for r in rows if r["keys"] == r["keys_in"]]
    return {
        "pack": len(rows),
        "inside": len(inside),
        "base": rows[0]["base"], "head": rows[0]["head"], "gap": rows[0]["gap"],
        "oldest": min(r["born"] for r in rows),
        "newest": max(r["born"] for r in rows),
        "runs": sum(r["runs"] for r in rows),
    }


if __name__ == "__main__":
    got = samples()
    for name, rows in sorted(got.items()):
        print("%-12s %d rows, %d positive" % (name, len(rows), sum(1 for _r, y in rows if y)))
