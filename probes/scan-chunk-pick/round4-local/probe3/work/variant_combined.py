"""Variant: dictionary knowledge combined with the page bounds (entries within bounds)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app")); sys.path.insert(0, HERE)
import ref
class RefC(ref.Ref):
    def dct(self, ch, pg, cd):
        lo, hi = self.bounds(pg)
        ents = [e for e in ch.dic if lo <= e <= hi]
        good = [e for e in ents if ref.sat(cd, e)]
        if not good:
            return False
        if len(good) == len(ents) and pg.nulls == 0:
            return True
        return None
def run(text):
    return RefC(text).run()
