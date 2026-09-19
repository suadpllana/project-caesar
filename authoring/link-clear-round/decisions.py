"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. Nothing here
re-implements the reference: the reference runs, and the rows are read off it by wrapping the
two calls the decisions pass through - the matcher, which is handed the parent's group with
every match, and the merge table, which is told every link that reaches a row.

The features are the raw ones the shipped tree exposes at the moment the decision is made: the
group of the row being carried, the link index, the child table's position, the kind of change,
and how many links have reached this row so far. Nothing says what the row's group will finally
be, because that is the thing being computed; nothing says which link was declared first among
those that reached a column, because the shipped tree meets them in an order that has nothing to
do with declaration order.

The verdict to want is that at least one graded quantity has no short rule. Two should not: the
group a row lands in, because a row met again by a longer chain moves and takes everything below
it along, and which link decides a column, because the reach meets the links out of order. Two
should be short, and honestly so: the direction the groups come out in is a stated rule with
nothing behind it, and so is which check stops a change.

    python3 tools/onelinecheck.py link-clear-round
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"group": [], "takes": [], "stops": [], "direction": []}


def _install(here):
    sys.path.insert(0, str(here))
    for name in [n for n in sys.modules if n == "run_keep" or n == "keep"
                 or n.startswith("keep.")]:
        del sys.modules[name]
    import run_keep
    from keep import hit, lay, meld, reach
    return run_keep, hit, lay, meld, reach


def _wrap(run_keep, hit, lay, meld, reach):
    """Record the decisions the reference makes, without changing any of them."""
    base_kids = hit.Find.kids
    base_col = meld.Meld.col
    base_drop = meld.Meld.drop
    base_walk = reach.walk
    base_run = lay.run
    seen = {"kind": 0, "match": [], "reach": {}, "hits": {}}

    def kids(self, link, keys):
        got = base_kids(self, link, keys)
        for ck in got:
            row = self.st.get(link.kid, ck)
            up = keys[row[link.ci]][0] if isinstance(keys, dict) else 0
            at = (link.kid, ck)
            seen["reach"][at] = seen["reach"].get(at, 0) + 1
            seen["match"].append((at, up, link.at, self.st.tabs[link.kid].at,
                                  seen["reach"][at]))
        return got

    def col(self, tab, key, ci, kind, val, li):
        seen["hits"].setdefault((tab, key, ci), []).append(li)
        return base_col(self, tab, key, ci, kind, val, li)

    def drop(self, tab, key, li):
        seen["hits"].setdefault((tab, key, -1), []).append(li)
        return base_drop(self, tab, key, li)

    def walk(work, kind, tab, key, new):
        seen["kind"] = 0 if kind == "out" else 1
        seen["match"] = []
        seen["reach"] = {}
        seen["hits"] = {}
        md, grp, bars = base_walk(work, kind, tab, key, new)
        for at, up, li, tat, nth in seen["match"]:
            if at not in grp:
                continue
            ROWS["group"].append(({"up": up, "next": up + 1, "li": li, "at": tat,
                                   "kind": seen["kind"], "nth": nth}, grp[at]))
        for (tab2, key2, ci), lis in seen["hits"].items():
            if len(lis) < 2:
                continue
            here = md.rows.get(tab2, {}).get(key2)
            if here is None:
                continue
            won = here.gone if ci < 0 else (here.cols.get(ci) or (None, None, None))[2]
            if won is None:
                continue
            ROWS["takes"].append(({"first": lis[0], "last": lis[-1], "n": len(lis),
                                   "kind": seen["kind"]}, won))
        moved = sum(1 for t in md.rows for k in md.rows[t] if md.newkey(t, k) is not None)
        waits = sum(1 for ln in work.links
                    if (ln.goes if kind == "out" else ln.moves) == "wait")
        seen["stop"] = ({"bars": len(bars), "moved": moved, "waits": waits,
                         "kind": seen["kind"]}, grp)
        ROWS["direction"].append(({"kind": seen["kind"],
                                   "groups": len(set(grp.values()))}, seen["kind"]))
        return md, grp, bars

    def run(work, op, out):
        before = len(out.lines)
        seen["stop"] = None
        base_run(work, op, out)
        fresh = out.lines[before:]
        if seen.get("stop") is None or not fresh:
            return
        head = fresh[-1].split()[0]
        label = {"bar": 1, "clash": 2, "wait": 3}.get(head, 0)
        ROWS["stops"].append((seen["stop"][0], label))

    hit.Find.kids = kids
    meld.Meld.col = col
    meld.Meld.drop = drop
    reach.walk = walk
    lay.run = run
    return run_keep


def samples():
    cases, gen, model = lab.sealed()
    here = lab.tree(lab.SOL)
    run_keep = _wrap(*_install(here))
    work = [cases.prog(name) for name in cases.ORDER]
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(14):
            work.append(gen.build(fam, random.Random("decide|%s|%d" % (fam, i))))
    for lines in work:
        got = run_keep.run("\n".join(lines) + "\n")
        assert got == model.expect(lines), "the watched copy drifted from the model"
    return ROWS
