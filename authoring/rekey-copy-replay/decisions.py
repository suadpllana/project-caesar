"""The graded decisions of this task as rows of integers the agent can already see.

The question `tools/onelinecheck.py` asks is not "is every rule covered" but "is the answer
short": a decision reproduced by one or two comparisons over fields the environment already
exposes is an answer a frontier model writes cold, before running anything.

Three of the four decisions here are deliberately short, and they are the conventions the
brief states outright - where the cursor lands, whether a pair is free, who takes a freed pair.
The one the task rests on is the entry verdict, and its inputs are the journal position, the
key, the cursor and whatever marks the shipped `Marks` exposes. The mark that actually decides
it belongs to the reach covering that key, which the shipped tree does not keep and no pair of
exposed fields reconstructs.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import gen  # noqa: E402
import model  # noqa: E402

VERDICT = {"ahead": 0, "seen": 1, "done": 2}


class Watched(model.Model):
    def __init__(self, chunk):
        super().__init__(chunk)
        self.rows = {"entry-verdict": [], "chunk-cursor": [], "pair-taken": [],
                     "free-winner": []}
        self.arrive = {}

    def copy(self):
        before = self.cur
        i = __import__("bisect").bisect_right(self.keys, self.cur)
        taken = self.keys[i:i + self.chunk]
        super().copy()
        if taken:
            self.rows["chunk-cursor"].append((
                {"cur": before, "chunk": self.chunk, "took": len(taken),
                 "largest": taken[-1], "top": before + self.chunk,
                 "live": len(self.keys)},
                self.cur))

    def play(self, n):
        stop = min(len(self.jrn), self.seen_upto + n)
        while self.seen_upto < stop:
            pos = self.seen_upto + 1
            _kind, k = self.jrn[self.seen_upto][:2]
            if k > self.cur:
                verdict = "ahead"
            elif pos <= self._mark_for(k):
                verdict = "seen"
            else:
                verdict = "done"
            self.rows["entry-verdict"].append((
                {"pos": pos, "k": k, "cur": self.cur, "depth": len(self.jrn),
                 "first": self.mark[0] if self.mark else 0,
                 "last": self.mark[-1] if self.mark else 0,
                 "reaches": len(self.mark)},
                VERDICT[verdict]))
            super().play(1)

    def _ask(self, k, a, b, c):
        self.rows["pair-taken"].append((
            {"k": k, "held": 1 if (a, b) in self.held else 0, "rows": len(self.row),
             "pairs": len(self.held), "waiting": sum(len(v) for v in self.wait.values())},
            0 if (a, b) in self.held else 1))
        if (a, b) in self.held:
            self.arrive.setdefault((a, b), []).append(k)
        super()._ask(k, a, b, c)

    def _free(self, key):
        line = list(self.wait.get(key) or ())
        came = [k for k in self.arrive.get(key, []) if k in line]
        super()._free(key)
        if line:
            self.arrive[key] = [k for k in came if k != min(line)]
            self.rows["free-winner"].append((
                {"asked_first": came[0] if came else min(line), "small": min(line),
                 "large": max(line), "many": len(line)},
                min(line)))


def samples():
    out = {"entry-verdict": [], "chunk-cursor": [], "pair-taken": [], "free-winner": []}
    for fam, _name, lines in gen.programs("decisions", 3):
        if fam in ("wide", "deep"):
            continue
        m = None
        for raw in lines:
            part = raw.split()
            head = part[0]
            if head == "cfg":
                m = Watched(int(part[1]))
            elif head == "set":
                m.write(int(part[1]), int(part[2]), int(part[3]), int(part[4]))
            elif head == "del":
                m.erase(int(part[1]))
            elif head == "copy":
                m.copy()
            elif head == "play":
                m.play(int(part[1]))
            elif head == "cut":
                m.cut()
        for key, rows in m.rows.items():
            out[key].extend(rows)
    return out
