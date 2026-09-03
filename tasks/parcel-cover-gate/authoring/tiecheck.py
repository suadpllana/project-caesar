"""No graded row may come down to a choice the submission was left to make alone.

Nothing here is named by a submission - parcels are numbered by the fabric,
settings and workers come out of the feed - so the free choices this task leaves
are orders and containers, and the useful question is which of them are free and
which are the rules. That question has a wrong answer that looks obvious, and
this file exists because the wrong answer was believed for an afternoon.

  NOT free, and it is graded: which of two ready parcels goes up. A shown map
  only moves onto versions standing after what it shows, which makes it easy to
  argue that anything ready stays ready. The argument fails for a setting the
  worker has never heard of: putting a version of it up puts every parcel
  carrying the other branch out of reach for good. So the earliest-handed one
  goes, `rival-parcels` pins it, and `cheat-latest-first` is a cheat rather than
  a variant.

  Free, and it must stay free: the order the entries of one parcel are written
  into the shown map, and what the bag is kept in. A parcel goes up whole, so
  nothing can observe the inside of that.

The nonces matter more than the count. The order case turns up in roughly one
generated feed in three hundred, so a single fixed nonce is a much weaker check
than it looks - which is exactly how the container caught what a local run with
one seed had called clean. Several nonces, every time.
"""

import os
import shutil
import sys
import tempfile

import lab

FREE = {
    "entries-as-they-come": {},
    "entries-sorted": {"gate.py": ("            for s in p:",
                                   "            for s in sorted(p):")},
    "entries-reversed": {"gate.py": ("            for s in p:",
                                     "            for s in sorted(p, reverse=True):")},
    "bag-as-a-copy": {"gate.py": ("        for no in list(bag):",
                                  "        for no in bag[:]:")},
}

SEEDS = ("tie-a", "tie-b", "tie-c", "tie-d", "tie-e", "tie-f")


def main(argv):
    each = int(argv[argv.index("--count") + 1]) if "--count" in argv else 100
    feeds = lab.named()
    for seed in SEEDS:
        feeds.update(lab.made(seed, each))
    hold = tempfile.mkdtemp(prefix="pcg-tie-")
    try:
        base = None
        bad = 0
        for name in sorted(FREE):
            over = dict(lab.reference())
            for fn, (old, new) in FREE[name].items():
                if old not in over[fn]:
                    raise SystemExit("anchor missing for %s" % name)
                over[fn] = over[fn].replace(old, new, 1)
            got = lab.play(lab.tree(os.path.join(hold, name), over), feeds)
            if base is None:
                base = got
                print("ok   %-22s %d feeds over %d nonces, the baseline"
                      % (name, len(feeds), len(SEEDS)))
                continue
            off = [n for n in sorted(feeds) if got[n] != base[n]]
            print("%s  %-22s %d feeds differ"
                  % ("ok " if not off else "BAD", name, len(off)))
            if off:
                print("     first: %s" % off[0])
                bad += 1
        print("\n%s" % ("no graded row turns on a choice the submission was left"
                        " to make" if not bad
                        else "A GRADED ROW TURNS ON A FREE CHOICE"))
        return 1 if bad else 0
    finally:
        shutil.rmtree(hold, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
