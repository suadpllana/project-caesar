"""Programs generated inside the verifier from a seed drawn after the agent's container is gone.

The enumerated set in `cases.py` pins each rule with a program small enough to read. This is the
other half of the grading: programs a submission cannot have seen, in families shaped around the
readings a per-rule set does not separate.

  plain    one volume writing, trimming and asking, with extents either side of the half rule
  dup      copies that leave several slots on one block, so a pointer tally and an occupancy
           figure part company
  share    two volumes on the same extents, trimmed on both sides, so the drop-gain question has
           a pair term to carry
  snap     a snapshot, trims in both volumes, then the snapshot dropped: extents become single
           held all at once and the rewrites happen in an op that wrote nothing
  three    a third volume on some extents, where dropping one still leaves the extent shared
  edge     extents whose occupancy sits exactly at or one block either side of half
  many     several files and volumes at once, with copies across them
  wide     the scale family: a large import asked many questions
  deep     the scale family: a large import shared, thinned on both sides and dropped, so
           thousands of extents are rewritten in one op

`wide` and `deep` are the families the execution limit is about. Everything else is small.
"""
import random

FAMILIES = (
    ("plain", False),
    ("dup", False),
    ("share", False),
    ("snap", False),
    ("three", False),
    ("edge", False),
    ("many", False),
    ("wide", True),
    ("deep", True),
)

SLOTS = 16


def _ask(rng, vols, out, n=2):
    for _ in range(n):
        v = rng.choice(vols)
        pick = rng.randrange(4)
        if pick == 0:
            out.append("use %s" % v)
        elif pick == 1:
            out.append("own %s" % v)
        elif pick == 2:
            out.append("tot")
        else:
            out.append("at %s p %d" % (v, rng.randrange(SLOTS)))


def _span(rng, hi=5):
    lo = rng.randrange(SLOTS)
    return lo, min(SLOTS - 1, lo + rng.randrange(hi))


def _plain(rng):
    out = ["vol a", "fil a p %d" % SLOTS]
    for _ in range(rng.randrange(8, 16)):
        lo, hi = _span(rng, 6)
        out.append("%s a p %d %d" % (rng.choice(["wr", "wr", "tr"]), lo, hi))
        _ask(rng, ["a"], out, rng.randrange(1, 3))
    _ask(rng, ["a"], out, 3)
    out.append("tot")
    return out


def _dup(rng):
    out = ["vol a", "fil a p %d" % SLOTS, "wr a p 0 %d" % (SLOTS - 1)]
    for _ in range(rng.randrange(6, 14)):
        pick = rng.randrange(3)
        if pick == 0:
            src = rng.randrange(SLOTS)
            dst = rng.randrange(SLOTS)
            out.append("cp a p %d %d a p %d" % (src, src, dst))
        elif pick == 1:
            lo, hi = _span(rng, 3)
            off = rng.randrange(SLOTS - (hi - lo))
            out.append("cp a p %d %d a p %d" % (lo, hi, off))
        else:
            lo, hi = _span(rng, 4)
            out.append("tr a p %d %d" % (lo, hi))
        _ask(rng, ["a"], out, 1)
    _ask(rng, ["a"], out, 3)
    out.append("tot")
    return out


def _share(rng):
    out = ["vol a", "fil a p %d" % SLOTS, "vol b", "fil b p %d" % SLOTS]
    out.append("wr a p 0 %d" % (SLOTS - 1))
    out.append("wr a p 0 %d" % rng.randrange(3, 9))
    lo, hi = 0, rng.randrange(2, 6)
    out.append("cp a p %d %d b p %d" % (lo, hi, rng.randrange(0, 4)))
    for _ in range(rng.randrange(6, 14)):
        v = rng.choice(["a", "b"])
        pick = rng.randrange(4)
        w = "b" if v == "a" else "a"
        if pick == 0:
            lo, hi = _span(rng, 5)
            out.append("tr %s p %d %d" % (v, lo, hi))
        elif pick == 1:
            lo, hi = _span(rng, 4)
            out.append("wr %s p %d %d" % (v, lo, hi))
        elif pick == 2:
            one = rng.randrange(SLOTS)
            out.append("cp %s p %d %d %s p %d" % (v, one, one, w, rng.randrange(SLOTS)))
            out.append("cp %s p %d %d %s p %d" % (v, one, one, w, rng.randrange(SLOTS)))
        else:
            lo, hi = _span(rng, 3)
            off = rng.randrange(SLOTS - (hi - lo))
            out.append("cp %s p %d %d %s p %d" % (v, lo, hi, w, off))
        _ask(rng, ["a", "b"], out, 2)
    for v in ("a", "b"):
        out += ["use %s" % v, "own %s" % v]
    out.append("tot")
    return out


def _snap(rng):
    out = ["vol a", "fil a p %d" % SLOTS, "wr a p 0 %d" % (SLOTS - 1)]
    out.append("wr a p 0 %d" % rng.randrange(2, 7))
    out.append("sn a b")
    for _ in range(rng.randrange(4, 9)):
        v = rng.choice(["a", "b"])
        lo, hi = _span(rng, 5)
        out.append("tr %s p %d %d" % (v, lo, hi))
        _ask(rng, ["a", "b"], out, 1)
    out += ["own a", "own b", "tot"]
    dead = rng.choice(["a", "b"])
    kept = "b" if dead == "a" else "a"
    out.append("rm %s" % dead)
    out += ["tot", "use %s" % kept, "own %s" % kept]
    for i in range(0, SLOTS, 5):
        out.append("at %s p %d" % (kept, i))
    out.append("tot")
    return out


def _three(rng):
    out = ["vol a", "fil a p %d" % SLOTS, "wr a p 0 %d" % (SLOTS - 1)]
    out += ["vol b", "fil b p %d" % SLOTS, "vol c", "fil c p %d" % SLOTS]
    lo, hi = 0, rng.randrange(2, 7)
    out.append("cp a p %d %d b p 0" % (lo, hi))
    out.append("cp a p %d %d c p 0" % (lo, rng.randrange(lo, hi + 1)))
    for _ in range(rng.randrange(5, 11)):
        v = rng.choice(["a", "b", "c"])
        lo, hi = _span(rng, 5)
        out.append("%s %s p %d %d" % (rng.choice(["tr", "tr", "wr"]), v, lo, hi))
        _ask(rng, ["a", "b", "c"], out, 2)
    dead = rng.choice(["b", "c"])
    out.append("rm %s" % dead)
    for v in ("a", "b", "c"):
        if v != dead:
            out += ["own %s" % v, "use %s" % v]
    out += ["at a p 0", "tot"]
    return out


def _edge(rng):
    siz = rng.randrange(2, 9)
    out = ["vol a", "fil a p %d" % SLOTS, "wr a p 0 %d" % (siz - 1)]
    keep = rng.randrange(1, siz + 1)
    if keep < siz:
        out.append("tr a p %d %d" % (keep, siz - 1))
    out += ["tot", "own a", "use a"]
    out.append("vol b")
    out.append("fil b p %d" % SLOTS)
    out.append("cp a p 0 %d b p 0" % rng.randrange(0, max(keep, 1)))
    out += ["own a", "own b", "tot"]
    lo, hi = _span(rng, 4)
    out.append("tr a p %d %d" % (lo, hi))
    out += ["own a", "own b", "use a", "use b", "tot"]
    out.append("rm b")
    out += ["tot", "own a", "at a p 0"]
    return out


def _many(rng):
    vols = ["a", "b"]
    out = ["vol a", "fil a p %d" % SLOTS, "fil a q %d" % SLOTS, "vol b", "fil b p %d" % SLOTS]
    out.append("wr a p 0 %d" % (SLOTS - 1))
    out.append("wr a q 0 %d" % rng.randrange(4, SLOTS))
    for _ in range(rng.randrange(8, 16)):
        v = rng.choice(vols)
        f = "p" if v == "b" else rng.choice(["p", "q"])
        pick = rng.randrange(5)
        if pick == 0:
            lo, hi = _span(rng, 5)
            out.append("wr %s %s %d %d" % (v, f, lo, hi))
        elif pick == 1:
            lo, hi = _span(rng, 5)
            out.append("tr %s %s %d %d" % (v, f, lo, hi))
        elif pick == 2:
            lo, hi = _span(rng, 3)
            off = rng.randrange(SLOTS - (hi - lo))
            w = rng.choice(vols)
            g = "p" if w == "b" else rng.choice(["p", "q"])
            out.append("cp %s %s %d %d %s %s %d" % (v, f, lo, hi, w, g, off))
        elif pick == 3 and "s" not in vols:
            out.append("sn a s")
            vols.append("s")
        else:
            _ask(rng, vols, out, 2)
        _ask(rng, vols, out, 1)
    for v in vols:
        out += ["use %s" % v, "own %s" % v]
    out.append("tot")
    return out


def _wide(rng):
    n = rng.randrange(50000, 70001, 5000)
    w = rng.randrange(3, 6)
    share = rng.randrange(600, 1400, 200)
    ops = 18000
    out = ["vol v", "bulk v p %d %d" % (n, w), "vol u", "fil u q %d" % (share * w)]
    out.append("cp v p 0 %d u q 0" % (share * w - 1))
    at = 0
    while len(out) < ops:
        base = at * w
        out.append("tr v p %d %d" % (base + 1, base + w - 1))
        out += ["use v", "own v", "tot", "use u", "own u"]
        at = (at + 1) % n
    out.append("at v p 0")
    return out


def _deep(rng):
    n = rng.randrange(25000, 35001, 5000)
    w = 8
    cuts = rng.randrange(4000, 6001, 500)
    out = ["vol v", "bulk v p %d %d" % (n, w), "sn v w"]
    for i in range(cuts):
        base = i * w
        out.append("tr v p %d %d" % (base + 3, base + w - 1))
    for i in range(cuts):
        base = i * w
        out.append("tr w p %d %d" % (base + 3, base + w - 1))
    out += ["tot", "own v", "own w"]
    out.append("rm w")
    out += ["tot", "use v", "own v", "at v p 0", "at v p 3"]
    return out


MAKE = {
    "plain": _plain,
    "dup": _dup,
    "share": _share,
    "snap": _snap,
    "three": _three,
    "edge": _edge,
    "many": _many,
    "wide": _wide,
    "deep": _deep,
}


def programs(seed, per, big=3):
    """Every graded nonce program: (family, name, lines), in a fixed order."""
    out = []
    for fam, heavy in FAMILIES:
        count = big if heavy else per
        for i in range(count):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), MAKE[fam](rng)))
    return out
