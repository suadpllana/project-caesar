"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The rows come from
`brute.Pane`, the brief transcribed literally, because its state is plain; every sampled
document is replayed through the reference as well and the two outputs must be identical, so
the decisions recorded are the reference's.

The features are the raw ones a solver has in hand at that moment: what the shipped tree keeps
(a row's own real height, the estimate, whether a row was ever measured, a group's header height)
and what the brief's memory adds (whether a row is remembered now, the last pass that saw it, its
place in the flow and in the window). Nothing derived is offered - not the height carried into a
row, not the oldest stamp in the memory, not the rows a sweep has given up - because the
derivation is the task.

Five questions. Two are stated one-line rules and are expected to come out short: whether the
hold steps back off the line (the item there is a row the pane does not remember), and whether
the band is pushed (the next header is nearer than this one is tall). The other three are the
ones the first submission answered cold and this one should not: the height a row stands at,
which in the first submission was by definition its own height once measured and the estimate
before; whether a pass measures a row, which depends on the memory at the moment the sweep gets
there rather than when the pass began; and which row the memory gives up.

    python3 authoring/row-anchor-pass/decisions.py
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TESTS = HERE.parents[1] / "tasks" / "row-anchor-pass" / "tests"
sys.path.insert(0, str(TESTS))

import brute  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402

SMALL = [fam for fam, big in gen.FAMILIES if not big]
PER = 12
CAP = 1500


class Probe(brute.Pane):
    """brute.Pane, recording each decision as it is made. It changes nothing it observes."""

    def __init__(self, cfg, decls, out):
        super().__init__(cfg, decls)
        self.out = out
        self.ever = set()
        self.cur = None

    def _index(self):
        return {it[2]: i for i, it in enumerate(self.items()) if it[0] == "R"}

    def take(self, line):
        its, hs, tops, total = self.geo()
        i = self.at(tops, hs, total, line)
        kind, _gi, rid = its[i]
        row = {
            "line_is_header": int(kind == "H"),
            "line_remembered": int(kind == "R" and rid in self.rem),
            "line_ever_measured": int(kind == "R" and rid in self.ever),
            "line_is_last": int(i == len(its) - 1),
        }
        got = super().take(line)
        self.out["hold_steps_back"].append((row, got[0] != i))
        return got

    def band(self, off):
        pin, b = super().band(off)
        its, hs, tops, total = self.geo()
        heads = [i for i, it in enumerate(its) if it[0] == "H"]
        nxt = tops[heads[pin + 1]] if pin + 1 < len(heads) else total
        hh = self.gs[pin]["hh"]
        row = {"header": hh, "room": nxt - off, "pinned_top": tops[heads[pin]], "offset": off}
        self.out["band_pushed"].append((row, b < hh))
        return pin, b

    def window(self, off):
        self._flush()
        w0, w1 = super().window(off)
        its = self.items()
        rids = [its[i][2] for i in range(w0, w1 + 1) if its[i][0] == "R"]
        self.cur = {"w0": w0, "w1": w1, "rids": rids, "start": set(self.rem),
                    "ever": set(self.ever), "got": set()}
        return w0, w1

    def remember(self, rid, idx):
        if len(self.rem) >= self.C:
            victim = min(self.rem, key=lambda r: self.rem[r])
            where = self._index()
            w0, w1 = self.cur["w0"], self.cur["w1"]
            for r, (seen, _at) in self.rem.items():
                row = {
                    "last_seen": seen,
                    "now": self.passno,
                    "index": where[r],
                    "in_window": int(w0 <= where[r] <= w1),
                    "measuring_index": idx,
                }
                self.out["forgotten"].append((row, r == victim))
        super().remember(rid, idx)
        self.ever.add(rid)
        self.cur["got"].add(rid)

    def _flush(self):
        cur, self.cur = self.cur, None
        if cur is None:
            return
        rids = cur["rids"]
        before = 0
        for pos, rid in enumerate(rids):
            row = {
                "remembered_at_start": int(rid in cur["start"]),
                "ever_measured": int(rid in cur["ever"]),
                "pos_in_window": pos,
                "window_rows": len(rids),
                "unremembered_before": before,
                "memory_at_start": len(cur["start"]),
                "cap": self.C,
            }
            self.out["measured_by_pass"].append((row, rid in cur["got"]))
            if rid not in cur["start"]:
                before += 1

    def frame(self, ev):
        line = super().frame(ev)
        self._flush()
        its, hs, tops, total = self.geo()
        for i, (kind, gi, rid) in enumerate(its):
            if kind != "R":
                continue
            real = self.real(gi, rid)
            prev = its[i - 1]
            row = {
                "real": real,
                "estimate": self.E,
                "own": real if rid in self.rem else self.E,
                "shipped": real if rid in self.ever else self.E,
                "header": self.gs[gi]["hh"],
                "prev_real": self.real(prev[1], prev[2]) if prev[0] == "R" else -1,
            }
            self.out["row_height"].append((row, hs[i]))
        return line


def _documents():
    for fam in SMALL:
        for i in range(PER):
            rng = random.Random("decisions|%s|%d" % (fam, i))
            yield fam, gen.MAKERS[fam](rng)


def samples():
    out = {k: [] for k in ("hold_steps_back", "band_pushed", "row_height",
                           "measured_by_pass", "forgotten")}
    ref = lab.pane("solution")
    for fam, lines in _documents():
        cfg, decls, evs = brute.parse(lines)
        probe = Probe(cfg, decls, out)
        got = [probe.frame(ev) % n for n, ev in enumerate(evs)]
        got.append("end s %d t %d m %d" % (probe.off, probe.geo()[3], probe.meas))
        want = ref(lines)
        assert got == want, "brute and the reference disagree on a %s document" % fam
    rng = random.Random("decisions|thin")
    for k, rows in out.items():
        if len(rows) > CAP:
            out[k] = rng.sample(rows, CAP)
    return out


if __name__ == "__main__":
    got = samples()
    for k, v in sorted(got.items()):
        print("%-18s %5d rows, %d distinct labels" % (k, len(v), len({str(y) for _, y in v})))
