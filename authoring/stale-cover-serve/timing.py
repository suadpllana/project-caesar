"""What the scale families cost the reference and what they cost the naive families.

The gate is only real once it is measured, and the number that matters is the slowest
plausible correct engine against the clock in tests/test.sh, not the reference against
itself. Three engines are timed:

    ref     the reference
    seek    the reference with the serving question answered by walking every version from
            the present one down to the allowance floor - exactly correct, and the shape a
            first implementation has
    scan    the reference with invalidation and retention walking the whole table on every
            commit instead of the key index - also exactly correct

    python -u authoring/stale-cover-serve/timing.py
"""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

SEEK = '''
def at(tb, lo, hi, s, now):
    floor = now - s
    if floor < 0:
        floor = 0
    for v in range(now, floor - 1, -1):
        need = set(range(lo, hi + 1))
        for st in tb.near(lo, hi):
            if st.born > v:
                continue
            if 0 <= st.died < v:
                continue
            a = st.lo if st.lo > lo else lo
            b = st.hi if st.hi < hi else hi
            for k in range(a, b + 1):
                need.discard(k)
            if not need:
                break
        if not need:
            return v
    return None
'''

SCAN_SEG = None


def scan_seg():
    src = (lab.SOL / "seg.py").read_text(encoding="utf-8")
    src = src.replace("""    def close(self, keys, upto):
        for k in keys:
            b = k // BLOCK
            box = self.opens.get(b)
            if not box:
                continue
            keep = []
            for st in box:
                if st.died >= 0 or st.gone:
                    continue
                if st.lo <= k <= st.hi:
                    st.died = upto
                    self.seq += 1
                    heapq.heappush(self.pend, (upto, self.seq, st))
                else:
                    keep.append(st)
            self.opens[b] = keep

    def drop(self, floor):
        pend = self.pend
        while pend and pend[0][0] < floor:
            heapq.heappop(pend)[2].gone = True
""", """    def close(self, keys, upto):
        for st in self.every():
            if st.died >= 0 or st.gone:
                continue
            for k in keys:
                if st.lo <= k <= st.hi:
                    st.died = upto
                    break

    def drop(self, floor):
        for st in self.every():
            if 0 <= st.died < floor:
                st.gone = True

    def every(self):
        seen = set()
        out = []
        for box in self.alls.values():
            for st in box:
                if id(st) not in seen:
                    seen.add(id(st))
                    out.append(st)
        return out
""")
    assert "def every(self)" in src, "seg.py drifted; the scan variant patch no longer applies"
    return src


def timed(tree, text):
    start = time.time()
    lab.run_text(tree, text)
    return time.time() - start


def main():
    gen = lab.gen()
    work = [row for row in gen.programs("timing", 1) if row[0] in ("wide", "deep")]
    trees = {
        "ref": lab.tree(lab.SOL),
        "seek": lab.tree(lab.SOL, {"pick.py": SEEK}),
        "scan": lab.tree(lab.SOL, {"seg.py": scan_seg()}),
    }
    totals = {k: 0.0 for k in trees}
    print("%-10s %8s %8s %8s" % ("program", "ref", "seek", "scan"))
    for fam, name, lines in work:
        text = "\n".join(lines) + "\n"
        row = []
        for key in ("ref", "seek", "scan"):
            if key == "seek" and fam == "deep":
                row.append(float("inf"))
                continue
            took = timed(trees[key], text)
            totals[key] += took
            row.append(took)
        print("%-10s %8.2f %8s %8.2f"
              % (name, row[0], "n/a" if row[1] == float("inf") else "%.2f" % row[1], row[2]))
    print("totals     %8.2f %8.2f %8.2f" % (totals["ref"], totals["seek"], totals["scan"]))
    print("(seek is not run on the deep family: one program did not finish in 20 minutes)")


if __name__ == "__main__":
    main()
