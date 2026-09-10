"""The graded decisions of the reference, as rows a short rule could be fitted to.

`tools/onelinecheck.py` searches for an exact rule of at most two comparisons over these
features. A task where every graded quantity has one is a task whose answer a model writes
before it runs anything. The features here are what the agent can read at the moment the
decision is made - counts on the span, the free total, the size of the request - not the
derivations the rules actually turn on, because a derivation offered as a feature is the
answer handed over.
"""
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "span-claim-charge"
PARTS = ("dev.py", "hold.py", "item.py", "line.py", "tally.py")


def stage():
    room = pathlib.Path(tempfile.mkdtemp())
    tree = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", tree,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for part in PARTS:
        shutil.copy(TASK / "solution" / part, tree / "store" / part)
    return tree


def programs():
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    import gen
    out = [cases.ops(name) for name in cases.ORDER]
    for fam, _name, lines in gen.programs("decide", 8):
        if fam in ("wide", "churn"):
            continue
        out.append(lines)
    return out


def samples():
    tree = stage()
    sys.path.insert(0, str(tree))
    from base import feed
    from store import dev, hold, item, tally

    rows = {"in-place": [], "span-back": [], "excl-gain": [], "write-refused": [],
            "alloc-pieces": []}

    real_bare = hold.bare

    def bare(cl, lo, hi):
        out = real_bare(cl, lo, hi)
        sp = cl.sp
        rows["in-place"].append(({
            "claims_on_span": len(sp.on),
            "lines_on_span": len(sp.by),
            "own_claims_here": sp.by.get(cl.own.line, 0),
            "span_wide": sp.wide,
            "window": hi - lo,
            "claim_wide": cl.wide,
        }, out == [(lo, hi)]))
        return out

    real_sweep = hold.sweep

    def sweep(st, touched):
        seen = set()
        for sp in touched:
            if sp in seen:
                continue
            seen.add(sp)
            rows["span-back"].append(({
                "claims_left": len(sp.on),
                "lines_left": len(sp.by),
                "span_wide": sp.wide,
            }, not sp.on))
        return real_sweep(st, touched)

    real_gain = tally.gain

    def gain(st, name, sp):
        rows["excl-gain"].append(({
            "lines_on_span": len(sp.by),
            "claims_on_span": len(sp.on),
            "own_claims_here": sp.by.get(name, 0),
            "span_wide": sp.wide,
        }, len(sp.by) == 1))
        return real_gain(st, name, sp)

    real_take = dev.take

    def take(st, want):
        free = dev.total(st)
        runs = dev.stat(st)
        out = real_take(st, want)
        rows["alloc-pieces"].append(({
            "want": want,
            "free": free,
            "runs": runs[1],
            "big": runs[2],
        }, 0 if out is None else len(out)))
        return out

    real_write = item.write

    def write(st, ln, nm, at, n):
        free = dev.total(st)
        kit = st.lines.get(ln) or {}
        it = kit.get(nm)
        out = real_write(st, ln, nm, at, n)
        rows["write-refused"].append(({
            "want": n,
            "free": free,
            "at": at,
            "size": it.size if it is not None else 0,
            "claims": len(it.cl) if it is not None else 0,
        }, out == "noroom"))
        return out

    hold.bare = bare
    hold.sweep = sweep
    tally.gain = gain
    dev.take = take
    item.write = write

    for lines in programs():
        feed.run(lines)

    hold.bare = real_bare
    hold.sweep = real_sweep
    tally.gain = real_gain
    dev.take = real_take
    item.write = real_write
    shutil.rmtree(tree.parent, ignore_errors=True)
    return rows
