"""Variant: the key's live rows exclude rows updated in the column."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app")); sys.path.insert(0, HERE)
import ref
from scn import emit
class RefS(ref.Ref):
    def run(self):
        seg = self.seg
        for qi, q in enumerate(self.queries):
            self.out.append("qry %d" % qi)
            self.alive = set(range(seg.n)) - seg.gone
            self.q = q
            self.sweep()
            while True:
                best = None
                for cd in q.conds:
                    up = seg.up[cd.c]
                    for ch in seg.cols[cd.c]:
                        if not self.pending(cd, ch):
                            continue
                        live = sum(1 for r in range(ch.start, ch.start + ch.n) if r in self.alive and r not in up)
                        cnt = sum(self.pagecount(pg, cd) for pg in ch.pages)
                        key = (min(live, cnt), cd.pos, ch.j)
                        if best is None or key < best[0]:
                            best = (key, cd, ch)
                if best is None:
                    break
                self.apply(best[1], best[2])
            rows = sorted(self.alive)
            self.out.append("sel %d %d" % (len(rows), emit.digest(rows)))
            for c in q.cols:
                self.report(c)
        return self.out
def run(text):
    return RefS(text).run()
