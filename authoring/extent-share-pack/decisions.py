"""Rows for the short-answer audit: every graded quantity, as the reference decides it.

Each row is the state an agent could read at the moment the decision is made - the extent's size,
how many of its blocks are occupied, how many volumes are on it, how many pointers it carries, and
how many of its blocks the volume in question and the other volume occupy - together with what the
reference chose. Nothing derived is offered as a feature, because a derived feature would be the
answer handed over.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "extent-share-pack"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import gen  # noqa: E402
import model  # noqa: E402


class Watch(model.M):
    """The model, stopped at each decision long enough to write down what it saw."""

    def __init__(self, rows):
        super().__init__()
        self.rows = rows

    def feat(self, eid, me=None):
        on = self.von[eid]
        other = [v for v in on if v != me]
        return {
            "siz": self.siz[eid],
            "occ": self.occ[eid],
            "nv": len(on),
            "ptr": sum(1 for _ in self.ref[eid]),
            "mine": self.vocc.get((eid, me), 0) if me else 0,
            "other": self.vocc.get((eid, other[0]), 0) if len(other) == 1 else 0,
        }

    def after(self):
        for eid in sorted(self.hot):
            if eid not in self.siz:
                continue
            self.rows["given-up"].append((self.feat(eid), self.occ[eid] == 0))
            if self.occ[eid] == 0:
                continue
            fit = len(self.von[eid]) == 1 and 2 * self.occ[eid] < self.siz[eid]
            self.rows["rewritten"].append((self.feat(eid), fit))
            if fit:
                self.rows["new-size"].append((self.feat(eid), self.occ[eid]))
        super().after()

    def ex(self, a):
        if a[0] in ("use", "own"):
            me = a[1]
            for eid in sorted(self.siz):
                if me not in self.von[eid]:
                    continue
                f = self.feat(eid, me)
                if a[0] == "use":
                    self.rows["charge"].append((f, self.siz[eid]))
                else:
                    self.rows["drop-gain"].append((f, self.drop(eid, me)))
        super().ex(a)

    def drop(self, eid, me):
        """What this extent alone would give back if `me` were dropped next."""
        on = self.von[eid]
        if on == {me}:
            return self.siz[eid]
        if len(on) != 2:
            return 0
        other = next(v for v in on if v != me)
        left = self.vocc[(eid, other)]
        return self.siz[eid] - left if 2 * left < self.siz[eid] else 0


def samples():
    rows = {"given-up": [], "rewritten": [], "new-size": [], "charge": [], "drop-gain": []}
    for _fam, _name, lines in gen.programs("decisions", 5, big=0):
        watch = Watch(rows)
        for line in lines:
            a = tuple(line.split())
            if a:
                watch.ex(a)
    return {name: rows[name][:4000] for name in rows}
