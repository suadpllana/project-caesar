"""The gate, measured on the built tree.

Three correct families are timed against the reference on the shipped wide plan's own shape:
the shipped walking feeder, the same feeder with the semantics corrected (`slow/walk/`), and
the one that derives the pattern counts but still walks each source's own stream
(`slow/stream/`). A prefix is timed and the full plan extrapolated where a full run would take
longer than this is worth.
"""
from __future__ import annotations

import pathlib
import re
import sys
import time

import lab

HERE = pathlib.Path(__file__).resolve().parent


def prefix(text, steps):
    """The wide plan cut down to `steps` steps, keeping one show at the end."""
    out = []
    for line in text.splitlines():
        if line.startswith("take r "):
            out.append("take r %d" % steps)
        elif line.startswith("show r "):
            out.append("show r %d 5 2" % (steps - 1))
        elif line.split()[0] in ("load", "save", "feed", "take", "show"):
            continue
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def timed(policy, text, label, limit=900):
    t0 = time.time()
    try:
        lab.run(policy, text)
    except Exception as exc:
        print("   %-28s failed: %s" % (label, str(exc)[:120]), flush=True)
        return None
    took = time.time() - t0
    print("   %-28s %8.2f s" % (label, took), flush=True)
    return took


def main():
    wide = (lab.APP / "plans" / "wide.txt").read_text(encoding="utf-8")
    steps = int(re.search(r"^take r (\d+)$", wide, re.M).group(1))
    slots = steps * 256
    print("wide.txt: %d steps of 256 slots = %d slots" % (steps, slots), flush=True)

    print("full plan:", flush=True)
    full = timed(lab.reference(), wide, "reference (derives)")

    cut = 2000
    print("first %d steps (%d slots):" % (cut, cut * 256), flush=True)
    rows = []
    for label, policy in (("shipped walker", lab.shipped()),
                          ("walk, semantics fixed", HERE / "slow" / "walk"),
                          ("stream walk per source", HERE / "slow" / "stream")):
        if policy is not None and not pathlib.Path(policy).is_dir():
            print("   %-28s (not written yet)" % label, flush=True)
            continue
        took = timed(policy, prefix(wide, cut), label)
        if took:
            rows.append((label, took))
    print("extrapolated to the whole plan:", flush=True)
    for label, took in rows:
        print("   %-28s %8.0f s  (%.0fx the 60 s limit)"
              % (label, took * steps / cut, took * steps / cut / 60), flush=True)
    if full:
        print("reference headroom on this plan: %.0fx under the limit" % (60 / full), flush=True)


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main()
