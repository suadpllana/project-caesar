"""Definitional oracle for peg-hold-tally. Authoring only - never ships.

This is the semantics written the slowest, clearest way there is: a peg copies the volume's
whole slot map when it is made, and after every op the set of kept blocks is recomputed from
scratch. It is O(map) per peg and O(pegs * map) per op, so it can only be run on small
programs. Its job is to be obviously right, so that the reference (incremental) and the sealed
model (offline, two-pass) can both be checked against it, and to be the naive family the
resource gate is measured against.

Semantics, in one place:

  vol  v            v exists and holds nothing
  set  v x          a fresh block is allocated and slot x of v holds it
  clr  v x          slot x of v holds nothing
  dup  v d s        slot d of v holds whatever slot s of v holds
  peg  p v          p records v exactly as it stands
  shed p            p is gone
  fork w p          w exists and holds exactly what p holds
  back v x p y      slot x of v holds whatever p holds at slot y
  trim              every block nothing keeps and that was not printed before is printed
  tally p           how many blocks p keeps and nothing else keeps

A block is kept by a volume while any slot of that volume holds it, and by a peg while that peg
exists and its record holds it. A slot given the block it already holds is unchanged.
"""
import sys


class Slow:
    def __init__(self):
        self.vols = {}          # volume -> {slot: block}
        self.pegs = {}          # peg -> (volume, {slot: block})
        self.birth = {}         # block -> stamp
        self.blocks = []        # allocation order
        self.unkept = {}        # block -> stamp it stopped being kept
        self.printed = set()
        self.out = []
        self.stamp = 0

    # --- keeping -------------------------------------------------------------

    def kept(self):
        live = set()
        for slots in self.vols.values():
            live.update(slots.values())
        for _v, slots in self.pegs.values():
            live.update(slots.values())
        return live

    def settle(self):
        """Record the stamp at which each block stopped being kept, once."""
        live = self.kept()
        for b in self.blocks:
            if b not in live and b not in self.unkept:
                self.unkept[b] = self.stamp

    # --- ops -----------------------------------------------------------------

    def run(self, lines):
        for line in lines:
            bits = line.split()
            if not bits:
                continue
            self.stamp += 1
            getattr(self, "op_" + bits[0])(*bits[1:])
            self.settle()
        return self.out

    def op_vol(self, v):
        self.vols[v] = {}

    def op_set(self, v, x):
        b = "b%d" % (len(self.blocks) + 1)
        self.blocks.append(b)
        self.birth[b] = self.stamp
        self.vols[v][x] = b

    def op_clr(self, v, x):
        self.vols[v].pop(x, None)

    def op_dup(self, v, d, s):
        cur = self.vols[v].get(s)
        if cur is None:
            self.vols[v].pop(d, None)
        else:
            self.vols[v][d] = cur

    def op_peg(self, p, v):
        self.pegs[p] = (v, dict(self.vols[v]))

    def op_shed(self, p):
        self.pegs.pop(p)

    def op_fork(self, w, p):
        self.vols[w] = dict(self.pegs[p][1])

    def op_back(self, v, x, p, y):
        cur = self.pegs[p][1].get(y)
        if cur is None:
            self.vols[v].pop(x, None)
        else:
            self.vols[v][x] = cur

    def op_trim(self):
        ready = [b for b in self.blocks if b in self.unkept and b not in self.printed]
        ready.sort(key=lambda b: (self.unkept[b], self.blocks.index(b)))
        for b in ready:
            self.printed.add(b)
            self.out.append("gone %s" % b)

    def op_tally(self, p):
        v_slots = self.pegs[p][1]
        held = set()
        for slots in self.vols.values():
            held.update(slots.values())
        others = set()
        for name, (_v, slots) in self.pegs.items():
            if name != p:
                others.update(slots.values())
        mine = set(v_slots.values())
        self.out.append("tally %s %d" % (p, len(mine - held - others)))


def expect(lines):
    return Slow().run(lines)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        print("\n".join(expect([ln.rstrip("\n") for ln in fh if ln.strip()])))
