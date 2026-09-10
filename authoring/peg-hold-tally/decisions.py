"""The graded decisions as rows of features the agent can read, for tools/onelinecheck.py.

The features are things the shipped tree hands over without any of the reasoning the task is
about: how many slots hold the block now, how many volumes do, how many pegs stand, how old the
block is, how many blocks exist and how long it has been since the last trim. Nothing derived
from what is kept is offered, because the tree does not carry that either.
The labels are what the contract says: whether a block stopped being kept when a volume let it
go, what a tally prints, and how many blocks a trim gives back.

If a short rule over those features reproduces a label, the environment is answering the
question for the agent and the rule is not a discovery. The three quantities are collected from
a definitional settling of the contract, not from the reference, so the rows say what is true
rather than what one implementation happens to do.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "peg-hold-tally"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import slow  # noqa: E402


class Watch(slow.Slow):
    """The definitional settling, with the exposed state watched alongside it."""

    def __init__(self):
        super().__init__()
        self.rows = {"stops-being-kept": [], "tally-count": [], "trim-size": []}
        self.last_trim = 0

    def seen(self, b):
        """What the shipped tree shows about one block, without deriving anything."""
        slots = sum(1 for slots in self.vols.values() for got in slots.values() if got == b)
        vols = sum(1 for slots in self.vols.values() if b in slots.values())
        return {
            "slots_now": slots,
            "vols_now": vols,
            "pegs_live": len(self.pegs),
            "age": min(self.stamp - self.birth[b], 9),
            "blocks_total": min(len(self.blocks), 9),
        }

    def op_clr(self, v, x):
        got = self.vols[v].get(x)
        super().op_clr(v, x)
        self.note(got)

    def op_set(self, v, x):
        got = self.vols[v].get(x)
        super().op_set(v, x)
        self.note(got)

    def op_back(self, v, x, p, y):
        got = self.vols[v].get(x)
        super().op_back(v, x, p, y)
        self.note(got)

    def op_dup(self, v, d, s):
        got = self.vols[v].get(d)
        super().op_dup(v, d, s)
        self.note(got)

    def note(self, b):
        """A block just left a slot: does anything still keep it?"""
        if b is None or b in self.unkept:
            return
        self.rows["stops-being-kept"].append((self.seen(b), b not in self.kept()))

    def op_tally(self, p):
        v, snap = self.pegs[p]
        held = set()
        for slots in self.vols.values():
            held.update(slots.values())
        feats = {
            "pegs_live": len(self.pegs),
            "peg_holds": len(set(snap.values())),
            "vol_holds": len(set(self.vols[v].values())),
            "peg_holds_gone": len(set(snap.values()) - held),
            "blocks_total": min(len(self.blocks), 9),
        }
        before = len(self.out)
        super().op_tally(p)
        got = int(self.out[-1].split()[-1]) if len(self.out) > before else 0
        self.rows["tally-count"].append((feats, got))

    def op_trim(self):
        feats = {
            "slots_full": sum(len(slots) for slots in self.vols.values()),
            "since_last": min(self.stamp - self.last_trim, 9),
            "pegs_live": len(self.pegs),
            "blocks_total": min(len(self.blocks), 9),
        }
        before = len(self.out)
        super().op_trim()
        self.last_trim = self.stamp
        self.rows["trim-size"].append((feats, len(self.out) - before))


def samples():
    rows = {"stops-being-kept": [], "tally-count": [], "trim-size": []}
    for fam, _name, lines in gen.programs("decisions", 6):
        if fam not in gen.SMALL:
            continue
        w = Watch()
        w.run(lines)
        for key in rows:
            rows[key].extend(w.rows[key])
    return {k: v[:4000] for k, v in rows.items()}
