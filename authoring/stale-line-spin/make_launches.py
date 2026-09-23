"""Write the sample launches shipped in environment/app_src/launches/.

example.txt is the brief's worked example, found by example_search.py (it decides no cache,
residency or skipping reading - see that file for the floor it cannot avoid). The rest are one
launch of each kernel pattern the graded families draw from, from a fixed seed that is not a
grading seed: inputs to run and time, never answers. Nothing here prints an expected output.

Usage: python3 authoring/stale-line-spin/make_launches.py [--check]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "stale-line-spin"
sys.path.insert(0, str(TASK / "tests" / "seal"))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "environment" / "app_src"))
import gen  # noqa: E402
import model  # noqa: E402
from sim import load  # noqa: E402

OUT = TASK / "environment" / "app_src" / "launches"

EXAMPLE = """dev 2 1 1
grid 4
show 4 5
prog
brnz %bid rest
st [4] 2
out r2
exit
rest:
out r0
spin.cg r3 [5] ge 2
exit
"""

EXAMPLE_OUT = """blk 0 sm 0 at 0 end 3 0
hang 6
spin 1 sm 1 at 0 on 5 0
spin 2 sm 0 at 4 on 5 0
left 1
mem 4 2
mem 5 0"""

# file name -> generator family; the names are the kernel patterns the families are drawn from
SAMPLES = {
    "splitk_fixup.txt": "fixup",
    "grid_sync.txt": "barrier",
    "lookback_scan.txt": "chain",
    "tile_queue.txt": "queue",
    "logit_stats.txt": "stats",
    "tile_reduce.txt": "reduce",
    "splitk_wide.txt": "wide",
    "lookback_deep.txt": "deep",
    "persistent_reduce.txt": "stream",
}
SEED = "shipped-samples"


def texts():
    out = {"example.txt": EXAMPLE}
    for name, fam in SAMPLES.items():
        rng = random.Random("%s:%s" % (SEED, name))
        out[name] = "\n".join(gen.GEN[fam](rng)) + "\n"
    return out


def main():
    check = "--check" in sys.argv
    got = model.expect(EXAMPLE.strip("\n").split("\n"))
    assert got == EXAMPLE_OUT.split("\n"), got
    want = texts()
    bad = 0
    for name, text in sorted(want.items()):
        assert "\r" not in text and text.isascii(), name
        load.parse(text)
        path = OUT / name
        if check:
            if not path.is_file() or path.read_bytes() != text.encode():
                print("stale", name)
                bad += 1
            continue
        OUT.mkdir(exist_ok=True)
        path.write_text(text, encoding="ascii", newline="\n")
        assert b"\r" not in path.read_bytes()
    extra = sorted(p.name for p in OUT.glob("*") if p.name not in want)
    if extra:
        print("unexpected files:", extra)
        bad += 1
    print("%s %d launches" % ("checked" if check else "wrote", len(want)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
