"""Time the correct-but-naive families against the reference, on the programs that gate them.

The limit in the brief is only real once these numbers exist. Output is unbuffered on purpose:
a timing harness whose prints sit in a buffer behind the slow case looks exactly like a hang.

    python3 -u authoring/shard-redraw-resume/time_slow.py [--fam wide] [--cap 400]
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-redraw-resume"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(ROOT / "authoring" / "shard-redraw-resume"))
os.environ.setdefault("SRR_PRISTINE", str(TASK / "tests" / "pristine"))

import gen  # noqa: E402
import lab  # noqa: E402

SLOW = ROOT / "authoring" / "shard-redraw-resume" / "slow"


def main():
    fams = ("wide", "deep")
    if "--fam" in sys.argv:
        fams = (sys.argv[sys.argv.index("--fam") + 1],)
    cap = int(sys.argv[sys.argv.index("--cap") + 1]) if "--cap" in sys.argv else 400
    trees = {
        "ref": lab.tree(TASK / "solution"),
        "list": lab.tree(TASK / "solution", SLOW / "list"),
        "replay": lab.tree(TASK / "solution", SLOW / "replay"),
    }
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-slow-"))
    for fam, name, lines in gen.programs("agree-nonce", 1):
        if fam not in fams:
            continue
        path = room / (name + ".txt")
        path.write_text("\n".join(lines) + "\n", newline="\n")
        base = None
        for tag, here in trees.items():
            t = time.time()
            try:
                out = lab.run(here, path, timeout=cap)
                cost = time.time() - t
                same = "" if base is None or out == base else "  DIFFERS"
                if tag == "ref":
                    base = out
                print("  %-7s %8.2fs%s" % (tag, cost, same), flush=True)
            except subprocess.TimeoutExpired:
                print("  %-7s  over %ds" % (tag, cap), flush=True)
            except MemoryError:
                print("  %-7s  out of memory" % tag, flush=True)
        print("%s %s" % (name, lines[0]), flush=True)


if __name__ == "__main__":
    main()
