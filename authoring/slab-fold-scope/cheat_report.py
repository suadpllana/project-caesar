"""Which layer catches each cheat, not just that the reward came out 0.

A reward of 0 proves nothing on its own: a cheat can score 0 because its patch never applied,
because it crashed on the first program, or because the layer it was written to test never ran.
This runs every semantic cheat over the enumerated set and the generated families and names the
first program that catches it, times the three slow families against the stated limit, and
checks that the forgery reproduces every enumerated program and fails on one it could not have
seen. The isolation probes are graded by the container run, not here, and are listed as such.

    python3 authoring/slab-fold-scope/cheat_report.py [per]
"""
import os
import pathlib
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

LIMIT = 60
SEMANTIC = (
    emit.put_beside, emit.put_counts_all, emit.cut_width, emit.fold_all_inside,
    emit.fold_no_floor, emit.fold_overlap, emit.fold_restamp, emit.fold_slab_stamp,
    emit.fold_cached_minmax, emit.fold_own_in_reach, emit.mixed_ignore,
    emit.mixed_any_overlap, emit.mixed_whole_bucket, emit.mixed_keep,
    emit.mixed_no_renumber, emit.mixed_only_fold, emit.mixed_prescan,
    emit.parts_folds_last, emit.base_at_push, emit.number_always,
)
SLOW = ("slow-scan", "slow-per-key", "slow-copy")
PROBES = ("probe-answer-key", "probe-hijack-driver", "probe-plant-report",
          "probe-late-reward", "probe-crash-worker", "probe-malformed",
          "probe-privilege", "probe-shrink-set", "probe-rewrite-frozen")


def lay(files):
    room = pathlib.Path(tempfile.mkdtemp(prefix="sfs-cheat-"))
    for name, src in files.items():
        (room / name).write_text(src, encoding="utf-8", newline="\n")
    return room


def drive(here, lines, timeout=180):
    room = pathlib.Path(tempfile.mkdtemp(prefix="sfs-prog-"))
    prog = room / "p.txt"
    prog.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    try:
        return lab.run(here, prog, timeout=timeout)
    except Exception as exc:
        return ["RAISED %s" % exc]


def main():
    # The forgery finds the enumerated programs the way the worker does. Without this it
    # quietly degrades to its fallback reading here and the report measures the fallback.
    os.environ["SFS_TESTS"] = str(lab.TASK / "tests")
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    work = [("hand", n, cases.ops(n)) for n in cases.ORDER]
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(per):
            name = "%s-%d" % (fam, i)
            work.append((fam, name, gen.one(fam, "report/%s" % name)))
    truth = {name: model.expect(lines) for _f, name, lines in work}
    print("%d programs: %d enumerated, %d generated\n" % (
        len(work), len(cases.ORDER), len(work) - len(cases.ORDER)), flush=True)

    bad = []
    for build in SEMANTIC:
        emit.BUILT.clear()
        build()
        name, files = next(iter(emit.BUILT.items()))
        here = lab.tree(lay(files))
        caught = None
        for _fam, prog, lines in work:
            if drive(here, lines) != truth[prog]:
                caught = prog
                break
        if caught is None:
            bad.append(name)
            print("   %-22s NOT CAUGHT by any program" % name, flush=True)
        else:
            kind = "case" if caught in cases.PROGS else "generated"
            print("   %-22s caught by %-18s (%s)" % (name, caught, kind), flush=True)

    print(flush=True)
    big = [(fam, gen.one(fam, "report/%s-big" % fam)) for fam in ("wide", "deep")]
    for name in SLOW:
        files = {p: (HERE / "slow" / name[5:].replace("per-key", "perkey") / p)
                 for p in emit.PARTS}
        merged = {p: (src.read_text(encoding="utf-8") if src.is_file()
                      else (lab.TASK / "solution" / p).read_text(encoding="utf-8"))
                  for p, src in files.items()}
        here = lab.tree(lay(merged))
        wrong = [n for _f, n, lines in work if drive(here, lines) != truth[n]]
        spent = 0.0
        for _fam, lines in big:
            start = time.time()
            got = drive(here, lines, timeout=LIMIT * 4)
            spent += time.time() - start
            if got and str(got[0]).startswith("RAISED"):
                spent = float("inf")
                break
        verdict = "out of memory" if spent == float("inf") else "%.0f s" % spent
        print("   %-22s %s on the small set, one wide plus one deep: %s (limit %d s for all)"
              % (name, "exact" if not wrong else "WRONG on %s" % wrong[:2], verdict, LIMIT),
              flush=True)

    print(flush=True)
    emit.BUILT.clear()
    emit.forge()
    files = emit.BUILT["forge-from-truth"]
    here = lab.tree(lay(files))
    hand_bad = [n for n in cases.ORDER if drive(here, cases.ops(n)) != truth[n]]
    seen_bad = [n for _f, n, lines in work
                if n not in cases.PROGS and drive(here, lines) != truth[n]]
    print("   %-22s reproduces %d of %d enumerated, fails %d of %d generated"
          % ("forge-from-truth", len(cases.ORDER) - len(hand_bad), len(cases.ORDER),
             len(seen_bad), len(work) - len(cases.ORDER)), flush=True)
    if hand_bad or not seen_bad:
        bad.append("forge-from-truth")

    print("\n   %d isolation probes are graded by the container run only: %s"
          % (len(PROBES), ", ".join(PROBES)), flush=True)
    print("\n%s" % ("every semantic cheat is caught by a named program"
                    if not bad else "NOT CAUGHT: %s" % bad), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
