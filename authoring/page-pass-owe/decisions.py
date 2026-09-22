#!/usr/bin/env python3
"""The graded decisions of this task as integer rows, for tools/onelinecheck.py.

The question that check asks is whether a graded decision is reproducible by a short exact
rule over values the agent can already see - because such a decision is one a frontier model
writes cold, however much prose surrounds it.

Four questions, each recorded from the sealed model driven over the generated families. The
features are what the service has in hand at that moment and nothing else: no feature is the
answer under another name, and none of them is the mark, the ledger order or the delivery
memory, because those are the structures the task is about rather than values it can read.

  scan       what the scan does with the row it is looking at
  ledger     whether the entry at the front of the ledger goes out or the draining stops
  owed       whether a row an edit touched now stands owed to a scroll
  unhanded   the closing count of rows in a scroll's view it has not been handed
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "page-pass-owe"

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import gen  # noqa: E402
import model  # noqa: E402

SCAN, LEDGER, OWED, UNHANDED = [], [], [], []

PASS_BY, HAND_OUT, TAKE_ANYWAY, STEP_OVER, STOP = 0, 1, 2, 3, 4


class Watched(model.Run):
    """The model's own rules, with each decision written down as it is taken."""

    def settle(self, sc, i):
        r = self.rows.get(i)
        if r is not None:
            OWED.append((
                {"same_tag": 1 if r[1] == sc.g else 0,
                 "at_or_before": 1 if (sc.mk is not None and (r[0], i) <= sc.mk) else 0,
                 "handed": 1 if i in sc.got else 0,
                 "row_weight": r[2],
                 "page_weight": sc.c,
                 "hold": self.hold},
                1 if self.owed_now(sc, i) else 0,
            ))
        model.Run.settle(self, sc, i)

    def page(self, s):
        sc = self.scrolls[s]
        gone = []
        left = sc.c

        while len(gone) < sc.n and left > 0:
            i = sc.led.front()
            if i is None:
                break
            w = self.rows[i][2]
            out = 0 if (w > left and gone) else 1
            LEDGER.append(({"row_weight": w, "weight_left": left,
                            "handed_so_far": len(gone), "row_limit": sc.n,
                            "page_weight": sc.c, "owed_rows": sc.led.count()}, out))
            if not out:
                break
            sc.led.rm(i)
            sc.got.add(i)
            gone.append(i)
            left = left - w if w <= left else 0

        over = 0
        for pl in self.view.walk(sc.g, sc.mk):
            if len(gone) >= sc.n or left <= 0 or over >= sc.c:
                break
            i = pl[1]
            had = 1 if i in sc.got else 0
            w = self.rows[i][2]
            held = self.standing()
            if had:
                verdict = PASS_BY
            elif w <= left:
                verdict = HAND_OUT
            elif not gone:
                verdict = TAKE_ANYWAY
            elif held + w <= self.hold:
                verdict = STEP_OVER
            else:
                verdict = STOP
            SCAN.append(({"row_weight": w, "weight_left": left,
                          "handed_so_far": len(gone), "row_limit": sc.n,
                          "stepped_over": over, "page_weight": sc.c,
                          "weight_owed": held, "hold": self.hold, "handed": had},
                         verdict))
            if verdict == PASS_BY:
                sc.mk = pl
                continue
            if verdict == HAND_OUT:
                sc.mk = pl
                sc.got.add(i)
                gone.append(i)
                left -= w
                continue
            if verdict == TAKE_ANYWAY:
                sc.mk = pl
                sc.got.add(i)
                gone.append(i)
                left = 0
                continue
            if verdict == STOP:
                break
            sc.mk = pl
            sc.led.add(i, w)
            over += w

        parts = ["pg", str(s)]
        for i in gone:
            parts.append(str(i))
        self.out.append(" ".join(parts))

    def close(self):
        for s in sorted(self.scrolls):
            sc = self.scrolls[s]
            size = sum(1 for _ in self.view.members(sc.g))
            unseen = sum(1 for i in self.view.members(sc.g) if i not in sc.got)
            UNHANDED.append(({"view_size": size, "handed_total": len(sc.got),
                              "owed_rows": sc.led.count(), "table_size": len(self.rows),
                              "row_limit": sc.n, "page_weight": sc.c}, unseen))
        model.Run.close(self)


def _run(text):
    run_ = None
    for raw in text.splitlines():
        f = raw.split()
        if not f:
            continue
        if f[0] == "cfg":
            run_ = Watched(int(f[1]))
            continue
        a = [int(x) for x in f[1:]]
        if f[0] == "row" or f[0] == "add":
            run_.add(a[0], a[1], a[2], a[3])
        elif f[0] == "move":
            run_.move(a[0], a[1])
        elif f[0] == "tag":
            run_.retag(a[0], a[1])
        elif f[0] == "drop":
            run_.drop(a[0])
        elif f[0] == "open":
            run_.open(a[0], a[1], a[2], a[3])
        elif f[0] == "next":
            run_.page(a[0])
    run_.close()


def samples():
    del SCAN[:], LEDGER[:], OWED[:], UNHANDED[:]
    for j in range(180):
        fam = gen.SMALL[j % len(gen.SMALL)]
        rng = random.Random("decisions/%s/%d" % (fam, j))
        _run("\n".join(gen._prog(rng, fam)) + "\n")
    return {"scan": list(SCAN), "ledger": list(LEDGER),
            "owed": list(OWED), "unhanded": list(UNHANDED)}


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        print("%-10s %6d samples, %d labels" % (name, len(rows), len({y for _, y in rows})))
