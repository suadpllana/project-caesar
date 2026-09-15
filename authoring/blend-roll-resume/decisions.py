"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features offered
are the raw ones the shipped tree holds at that moment - a source's counter, its weight, its
epoch, its cursor, its size, its cap, how many sources are live, how wide a step is. Nothing
derived is offered, because the derivation is the task: a ratio, a total consumption, a blend
signature and a draw count at an arbitrary distance are all things the solver has to build.

The verdict to want is that no graded quantity has an exact rule at depth two. Two of them
should be clearly out of reach whatever the sample: which draw retires a capped source, because
it turns on the product of an epoch and a size, and how many draws a source takes over a run,
because that is the schedule inverted.

    python3 authoring/blend-roll-resume/decisions.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "blend-roll-resume"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "environment" / "app_src"))

import gen  # noqa: E402
from mix import perm  # noqa: E402


class Watch:
    """The contract, run draw by draw, writing down what it saw at each decision."""

    def __init__(self):
        self.seed = 0
        self.names = []
        self.size = {}
        self.weight = {}
        self.cap = {}
        self.live = []
        self.epoch = {}
        self.cur = {}
        self.cnt = {}
        self.step = 0
        self.cfg = None
        self.mark = None
        self.pick_rows = []
        self.gone_rows = []
        self.stop_rows = []
        self.share_rows = []

    def rebase(self):
        for name in self.live:
            self.cnt[name] = 0

    def sig(self):
        return tuple(self.live), tuple(self.weight[n] for n in self.live)

    def who(self):
        best = None
        for name in self.live:
            if best is None:
                best = name
            elif self.cnt[name] * self.weight[best] < self.cnt[best] * self.weight[name]:
                best = name
        return best

    def draw(self, pos, record):
        if record and len(self.live) == 2:
            a, b = self.live
            self.pick_rows.append(({
                "cnt_a": self.cnt[a], "w_a": self.weight[a],
                "cnt_b": self.cnt[b], "w_b": self.weight[b],
                "pos": pos,
            }, self.live.index(self.who())))
        name = self.who()
        row = perm.order(self.seed, self.names.index(name), self.epoch[name], self.size[name])
        row[self.cur[name]]
        before = {"epoch": self.epoch[name], "cursor": self.cur[name],
                  "size": self.size[name], "cap": self.cap[name],
                  "cnt": self.cnt[name], "live": len(self.live)}
        self.cnt[name] += 1
        self.cur[name] += 1
        if self.cur[name] == self.size[name]:
            self.cur[name] = 0
            self.epoch[name] += 1
        gone = bool(self.cap[name] and self.epoch[name] >= self.cap[name])
        if record:
            self.gone_rows.append((before, gone))
        if gone:
            self.live.remove(name)
            self.rebase()
        return gone

    def ex(self, line, record=True):
        p = line.split()
        kind = p[0]
        if kind == "seed":
            self.seed = int(p[1])
        elif kind == "src":
            name = p[1]
            self.names.append(name)
            self.size[name] = int(p[2])
            self.weight[name] = int(p[3])
            self.cap[name] = int(p[4])
            self.live.append(name)
            self.epoch[name] = 0
            self.cur[name] = 0
            self.cnt[name] = 0
            self.rebase()
        elif kind == "wt":
            self.weight[p[1]] = int(p[2])
            self.rebase()
        elif kind == "run":
            self.cfg = (int(p[1]), int(p[2]), int(p[3]))
        elif kind == "save":
            self.mark = {"step": self.step, "epoch": dict(self.epoch), "cur": dict(self.cur),
                         "cnt": dict(self.cnt), "sig": self.sig(),
                         "live": len(self.live),
                         "wsum": sum(self.weight[n] for n in self.live)}
        elif kind == "stop":
            m = self.mark
            self.step = m["step"]
            for name in m["epoch"]:
                self.epoch[name] = m["epoch"][name]
                self.cur[name] = m["cur"][name]
                self.cnt[name] = m["cnt"][name]
            stands = self.sig() == m["sig"]
            if record:
                self.stop_rows.append(({
                    "live_now": len(self.live), "live_saved": m["live"],
                    "wsum_now": sum(self.weight[n] for n in self.live),
                    "wsum_saved": m["wsum"],
                    "declared": len(self.names),
                }, stands))
            if not stands:
                self.rebase()
            self.cfg = None
        elif kind == "go":
            ranks, micro, accum = self.cfg
            wide = ranks * micro * accum
            steps = int(p[1])
            first = self.live[0] if self.live else None
            took = dict(self.cnt)
            for _ in range(steps):
                for pos in range(wide):
                    self.draw(pos, record)
                self.step += 1
            if record and first is not None and first in self.live:
                self.share_rows.append(({
                    "weight": self.weight[first],
                    "wsum": sum(self.weight[n] for n in self.live),
                    "live": len(self.live),
                    "steps": steps,
                    "wide": wide,
                }, self.cnt[first] - took.get(first, 0)))
        elif kind == "feed":
            pass
        elif kind == "at":
            pass
        else:
            raise ValueError(kind)


def samples():
    small = [w for w in gen.programs("onelinecheck", 40) if w[0] != "big"]
    watch = Watch()
    pick, gone, stop, share = [], [], [], []
    for _fam, _name, lines in small:
        one = Watch()
        try:
            for line in lines:
                one.ex(line)
        except Exception:
            continue
        pick += one.pick_rows
        gone += one.gone_rows
        stop += one.stop_rows
        share += one.share_rows
    del watch
    return {
        "which source a draw goes to": _trim(pick),
        "does this draw retire the source": _trim(gone),
        "do the counters a stop puts back stand": _trim(stop),
        "how many draws a source takes over a go": _trim(share),
    }


def _trim(rows, cap=2000):
    """Keep every outcome represented, and sample across the whole stream.

    Truncating a draw stream drops the rare outcome, and taking a prefix of each outcome
    keeps only the draws near where it happens - both make the rule look shorter than it is.
    The rows are shuffled from a fixed seed before the split, so the sample spans the run and
    is still the same sample on every call.
    """
    import random
    by = {}
    for row in rows:
        by.setdefault(str(row[1]), []).append(row)
    share = max(1, cap // max(1, len(by)))
    out = []
    for key in sorted(by):
        group = list(by[key])
        random.Random(len(group)).shuffle(group)
        out += group[:share]
    return out


if __name__ == "__main__":
    for key, rows in sorted(samples().items()):
        outs = {str(y) for _r, y in rows}
        print("%-40s %5d rows, %d outcomes" % (key, len(rows), len(outs)))
