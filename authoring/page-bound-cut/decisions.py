"""The shape of this task's answer, for tools/onelinecheck.py.

Each row is one graded decision the reference makes, described by integers the agent can read
off the state in front of it at that moment - entry counts, key lengths, capacities, the
position of a page under its parent - and the value the reference chose. If a short exact rule
over those features reproduces the choice, the decision is one a model writes cold whatever the
prose around it says.

The features deliberately stop where the derivations begin: no row carries a page's stored
size, its common prefix, or the length of a dividing string, because those are the quantities
the task is about. A rule found over them would mean the answer is short; a rule found only
with them would mean nothing.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

_cases, gen, model = lab.sealed()


def gather(limit=900):
    cut_rows = []
    fit_rows = []
    side_rows = []
    sep_rows = []

    plan = model.Idx.plan
    size = model.Idx.size
    knit = model.Idx.knit
    divider = model.divider

    def spy_plan(self, node):
        pos, sep = plan(self, node)
        ents = self.ents(node)
        up = self.tab[node.up] if node.up is not None else None
        cut_rows.append(({
            "entries": len(ents),
            "kids": 0 if node.leaf else len(node.kids),
            "leaf": 1 if node.leaf else 0,
            "middle": len(ents) // 2,
            "firstlen": len(ents[0]),
            "lastlen": len(ents[-1]),
            "upentries": 0 if up is None else len(up.seps),
            "upkids": 0 if up is None else len(up.kids),
            "at": 0 if up is None else self.where(node),
            "cap": self.cap,
        }, pos))
        return pos, sep

    def spy_size(self, node):
        got = size(self, node)
        ents = self.ents(node)
        if ents:
            fit_rows.append(({
                "entries": len(ents),
                "kids": 0 if node.leaf else len(node.kids),
                "leaf": 1 if node.leaf else 0,
                "chars": sum(len(e) for e in ents),
                "firstlen": len(ents[0]),
                "lastlen": len(ents[-1]),
                "cap": self.cap,
                "floor": self.floor,
            }, bool(got > self.cap)))
        return got

    def spy_knit(self, node, out):
        n = len(out)
        host = self.tab[node.up]
        j = self.where(node)
        knit(self, node, out)
        took = 2
        for line in out[n:]:
            if line.startswith("join"):
                took = 0 if int(line.split()[1][1:]) == node.pid else 1
        side_rows.append(({
            "at": j,
            "kids": len(host.kids),
            "last": len(host.kids) - 1,
            "leaf": 1 if node.leaf else 0,
            "entries": len(self.ents(node)),
            "cap": self.cap,
            "floor": self.floor,
        }, took))

    def spy_div(low, high):
        got = divider(low, high)
        sep_rows.append(({
            "lowlen": len(low),
            "highlen": len(high),
            "shorter": min(len(low), len(high)),
            "gap": abs(len(low) - len(high)),
        }, len(got)))
        return got

    model.Idx.plan = spy_plan
    model.Idx.size = spy_size
    model.Idx.knit = spy_knit
    model.divider = spy_div
    try:
        for row in gen.FAMILIES:
            for seed in range(3):
                model.trace(gen.build(row, seed))
                if len(fit_rows) > limit * 8:
                    break
    finally:
        model.Idx.plan = plan
        model.Idx.size = size
        model.Idx.knit = knit
        model.divider = divider
    return cut_rows[:limit], fit_rows[:limit], side_rows[:limit], sep_rows[:limit]


def samples():
    cut_rows, fit_rows, side_rows, sep_rows = gather()
    return {
        "cut position": cut_rows,
        "is the page over capacity": fit_rows,
        "which neighbour a join takes": side_rows,
        "length of the dividing string": sep_rows,
    }
