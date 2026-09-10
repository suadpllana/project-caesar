"""The literal reading of rules 6 and 7, with nothing optimised.

Every live transaction is removed in turn and the sweep re-run, for every pending
request, after every step, over the whole service. This is the naive-but-correct family
the execution limit is there to kill; here it is the third opinion that tells us the
reference's candidate classes and the model's participant groups never change an answer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent
                       / "tasks" / "claim-raise-cut" / "tests" / "seal"))

import model  # noqa: E402


class Slow(model.Run):
    def judge(self):
        while True:
            rel = {}
            for t in list(self.tx.values()):
                if not t.live or t.req is None:
                    continue
                k = self.it[t.req.kn]
                if id(t.req) in {id(r) for r in model.sweep(k)}:
                    continue
                out = set()
                for u in self.tx.values():
                    if u.name == t.name or not u.live:
                        continue
                    if id(t.req) in {id(r) for r in model.sweep(k, u.name)}:
                        out.add(u.name)
                rel[t.name] = out
            ring = model._sccs(rel)
            if not ring:
                return
            best = None
            for name in ring:
                t = self.tx[name]
                key = (len(t.held), -t.req.seq, -t.num)
                if best is None or key < best[0]:
                    best = (key, t)
            self.kill(best[1])
            self.roll()


def trace(steps):
    return [" ".join(row) for row in Slow().feed(steps)]
