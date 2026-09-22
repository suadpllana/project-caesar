"""What each implementation costs on the two scale families, and on the whole graded set.

Output is unbuffered on purpose: a timing harness that buffers looks exactly like a hang.

    python3 -u authoring/pin-drift-redo/timing.py
"""
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, model = lab.sealed()

WHICH = (("reference", lab.TASK / "solution"),
         ("flat", HERE / "variants" / "flat"),
         ("eager", HERE / "variants" / "eager"),
         ("redo", HERE / "variants" / "redo"),
         ("cut", HERE / "variants" / "cut"))


def main():
    wide = gen.build_wide(random.Random("time|wide"))
    deep = gen.build_deep(random.Random("time|deep"))
    whole = [(name, lines) for _f, name, lines in gen.programs("time|set", 40)]
    print("wide %d lines, deep %d lines, whole set %d programs"
          % (len(wide), len(deep), len(whole)), flush=True)
    for name, room in WHICH:
        here = lab.tree(room)
        row = [name]
        for what, lines in (("wide", wide), ("deep", deep)):
            t0 = time.perf_counter()
            got = lab.run_text(here, "\n".join(lines))
            spent = time.perf_counter() - t0
            ok = got == model.expect(lines)
            row.append("%s %6.2f s %s" % (what, spent, "ok" if ok else "WRONG"))
        t0 = time.perf_counter()
        bad = 0
        for prog, lines in whole:
            if lab.run_text(here, "\n".join(lines)) != model.expect(lines):
                bad += 1
        row.append("whole set %6.2f s, %d wrong" % (time.perf_counter() - t0, bad))
        print("  %-10s %s" % (row[0], "  |  ".join(row[1:])), flush=True)


if __name__ == "__main__":
    main()
