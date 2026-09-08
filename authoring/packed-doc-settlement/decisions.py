"""Every hand case runs, and every wrong reading is caught by a hand case.

Two separate claims, both worth checking mechanically. The first is that the
reference and the sealed model agree on the enumerated corners. The second is the
one that actually matters: a reading of the brief that no small case rejects is a
decision the verifier only catches by luck of the generator, so the table below
must have no empty row.
"""
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "packed-doc-settlement"))
sys.path.insert(0, str(ROOT / "tasks" / "packed-doc-settlement" / "tests" / "seal"))

import harness  # noqa: E402
import cases  # noqa: E402
import model  # noqa: E402
import readings  # noqa: E402


def main():
    ref = harness.solution_tree()
    want = {}
    bad = 0
    for name in cases.ORDER:
        lines = cases.ops(name)
        exp, tight, near = model.margins(lines)
        got, err = ref.guarded(lines)
        want[name] = exp
        flag = ""
        if err is not None:
            flag = "REFERENCE RAISED %s" % err
        elif got != exp:
            flag = "REFERENCE DIFFERS FROM MODEL"
        elif tight < 1e-6 or near < 1e-3:
            flag = "MARGIN TOO TIGHT tight=%.3g near=%.3g" % (tight, near)
        if flag:
            bad += 1
        print("%-30s %2d lines  %s" % (name, len(exp), flag or "ok"))

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pds-dec-"))
    try:
        print()
        for rname in sorted(readings.READINGS):
            tree = harness.Tree(readings.build(rname, tmp), into=tmp / ("t-" + rname))
            caught = []
            for name in cases.ORDER:
                got, err = tree.guarded(cases.ops(name))
                if err is not None or got != want[name]:
                    caught.append(name)
            if not caught:
                bad += 1
            print("%-32s %s" % (rname, ", ".join(caught[:3]) or "NO HAND CASE CATCHES THIS"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())


# --- the contract tools/onelinecheck.py drives this module through -----------------

import gen  # noqa: E402


class Rec(model.Sim):
    """The sealed model, watched from outside, so no decision logic is duplicated here.

    Each step is taken by the model itself; what is recorded around the call is the
    state an agent could read at that moment - how much of each open document the run
    has consumed, how many documents settled, how much of a requeue allowance each has
    spent - together with the choice the model made. The question the tool then asks is
    whether the choice follows from those numbers alone.
    """

    def __init__(self):
        model.Sim.__init__(self)
        self.rows = {"step-is-taken": [], "document-settles": [],
                     "document-requeued": [], "step-clipped": []}

    def step(self, out):
        lo = self.cur
        mark = len(out)
        marks = len(self.margin)
        before = {}
        for d, _ in self.flow[:lo]:
            before[d] = before.get(d, 0) + 1
        c = self.cfg
        spent = dict((i, self.docs[i][3]) for i in range(len(self.docs)))

        model.Sim.step(self, out)

        hi = self.cur
        now = {}
        for d, _ in self.flow[lo:hi]:
            now[d] = now.get(d, 0) + 1
        printed = out[mark:]
        taken = bool(printed) and printed[0].startswith("up ")
        requeued = [ln.split()[1] for ln in printed if ln.startswith("rq ")]

        settled = []
        for d in sorted(now):
            name, n, t, _ = self.docs[d]
            total = before.get(d, 0) + now[d]
            done = total >= n and t >= 0
            if done:
                settled.append(d)
            self.rows["document-settles"].append((
                {"read_total": total, "read_now": now[d], "length": n,
                 "contributes": 1 if t >= 0 else 0}, bool(done)))

        self.rows["step-is-taken"].append((
            {"settled": len(settled), "batches": max(1, len(now)),
             "sequences": (hi - lo) // c["lim"], "taken_before": self.applied},
            bool(taken)))

        if taken:
            clipped = any(v > 0 for k, v in self.margin[marks:] if k == "clip")
            self.rows["step-clipped"].append((
                {"settled": len(settled), "taken_before": self.applied - 1,
                 "sequences": (hi - lo) // c["lim"], "cap": int(c["clip"])},
                bool(clipped)))
            for pos, d in enumerate(settled):
                name, n, t, _ = self.docs[d]
                self.rows["document-requeued"].append((
                    {"spent": spent.get(d, 0), "cap": c["cap"], "length": n,
                     "target": t, "settled": len(settled), "order": pos},
                    name in requeued))


def samples():
    rows = {"step-is-taken": [], "document-settles": [],
            "document-requeued": [], "step-clipped": []}
    for _, _, lines in gen.programs("onelinecheck", 20)[:120]:
        sim = Rec()
        out = []
        for ln in lines:
            sim.ex(tuple(ln.split()), out)
        for k, v in sim.rows.items():
            rows[k].extend(v)
    return dict((k, v[:400]) for k, v in rows.items())
