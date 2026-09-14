"""Which layer catches each cheat, not just that the reward came out 0.

A reward of 0 proves nothing on its own: a cheat can score 0 because its patch never applied,
because it crashed on the first program, or because the layer it was written to test never ran.
This runs every semantic cheat over the enumerated set and the generated families and names the
first program that catches it, checks that the forgery reproduces every enumerated program and
fails on ones it could not have seen, and lists the isolation probes as what they are - graded
by a container run and by nothing here.

    python3 -u authoring/shard-redraw-resume/cheat_report.py [per]
"""
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

os.environ.setdefault("SRR_PRISTINE", str(lab.TASK / "tests" / "pristine"))

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

SLOW = ("slow-order-list", "slow-replay")
PROBES = ("probe-answer-key", "probe-crash-worker", "probe-hijack-driver", "probe-late-reward",
          "probe-malformed", "probe-plant-report", "probe-privilege", "probe-rewrite-frozen",
          "probe-shrink-set")


def lay(files):
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-cheat-"))
    for name, src in files.items():
        (room / name).write_text(src, encoding="utf-8", newline="\n")
    return room


def drive(here, lines, timeout=180):
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-prog-"))
    prog = room / "p.txt"
    prog.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    try:
        return lab.run(here, prog, timeout=timeout)
    except Exception as exc:
        return ["RAISED %s" % exc]


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    work = [("hand", n, cases.ops(n)) for n in cases.ORDER]
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(per):
            name = "%s-%d" % (fam, i)
            work.append((fam, name, gen.one(fam, "report/%s" % name)))
    truth = {name: model.expect(lines) for _f, name, lines in work}
    print("%d programs: %d enumerated, %d generated\n"
          % (len(work), len(cases.ORDER), len(work) - len(cases.ORDER)), flush=True)

    bad = []
    for build in emit.SEMANTIC:
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
            print("   %-20s NOT CAUGHT by any program" % name, flush=True)
        else:
            kind = "case" if caught in cases.PROGS else "generated"
            print("   %-20s caught by %-16s (%s)" % (name, caught, kind), flush=True)

    print(flush=True)
    for name in SLOW:
        src = HERE / "slow" / ("list" if name.endswith("list") else "replay")
        merged = {p: ((src / p) if (src / p).is_file() else (lab.TASK / "solution" / p)
                      ).read_text(encoding="utf-8") for p in emit.PARTS}
        here = lab.tree(lay(merged))
        wrong = [n for _f, n, lines in work if drive(here, lines) != truth[n]]
        print("   %-20s %s on the small set; the limit is what separates it"
              % (name, "exact" if not wrong else "WRONG on %s" % wrong[:2]), flush=True)

    print(flush=True)
    emit.BUILT.clear()
    emit.forge_answer_key()
    here = lab.tree(lay(emit.BUILT["forge-answer-key"]))
    hand_bad = [n for n in cases.ORDER if drive(here, cases.ops(n)) != truth[n]]
    seen_bad = [n for _f, n, lines in work
                if n not in cases.PROGS and drive(here, lines) != truth[n]]
    print("   %-20s reproduces %d of %d enumerated, fails %d of %d generated"
          % ("forge-answer-key", len(cases.ORDER) - len(hand_bad), len(cases.ORDER),
             len(seen_bad), len(work) - len(cases.ORDER)), flush=True)
    if hand_bad or not seen_bad:
        bad.append("forge-answer-key")

    print("\n   %d isolation probes are graded by the container run only: %s"
          % (len(PROBES), ", ".join(PROBES)), flush=True)
    print("\n%s" % ("every semantic cheat is caught by a named program"
                    if not bad else "NOT CAUGHT: %s" % bad), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
