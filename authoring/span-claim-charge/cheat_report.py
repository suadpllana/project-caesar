"""Which layer catches each cheat, not just that the reward came out 0.

A reward of 0 proves nothing on its own: a cheat can score 0 because its patch never applied,
because it crashed on the first program, or because the layer it was written to test never ran.
This runs every semantic cheat over the enumerated set and the generated families and names the
first program that catches it, times the slow families against the stated limit over the whole
graded set, and checks that the forgery reproduces every enumerated program and fails on one it
could not have seen. The isolation probes are graded by the container run, not here, and are
listed as such.

    python3 authoring/span-claim-charge/cheat_report.py [per]
"""
import pathlib
import subprocess
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
SLOW = ("slow-family", "slow-charge", "slow-fit", "slow-sole")
PROBES = ("probe-answer-key", "probe-crash-worker", "probe-forge-report", "probe-hijack-driver",
          "probe-kill-grader", "probe-late-reward", "probe-malformed", "probe-plant-verdict",
          "probe-privilege", "probe-rewrite-frozen", "probe-shrink-set")


def lay(files):
    room = pathlib.Path(tempfile.mkdtemp(prefix="scc-cheat-"))
    for name, src in files.items():
        (room / name).write_text(src, encoding="utf-8", newline="\n")
    return room


def drive(here, lines, timeout=300):
    try:
        return lab.drive(here, lines, timeout=timeout)
    except Exception as exc:
        return ["RAISED %s" % str(exc)[:200]]


def whole_set(here, seed, per, cap):
    """The graded set the way the worker runs it, one process, against the wall clock."""
    script = '''
import sys, time
sys.path.insert(0, %r); sys.path.insert(0, %r)
import cases, gen
from base import feed
work = [("hand", n, cases.ops(n)) for n in cases.ORDER] + gen.programs(%r, %d)
t = time.time()
for _f, _n, lines in work:
    feed.run(lines)
print("%%.1f" %% (time.time() - t))
''' % (str(lab.TASK / "tests"), str(here), seed, per)
    t = time.time()
    try:
        out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                             timeout=cap, cwd=str(here))
    except subprocess.TimeoutExpired:
        return None
    if out.returncode != 0:
        return "failed: %s" % out.stderr.strip().splitlines()[-1][:80]
    return float(out.stdout.strip().splitlines()[-1])


def main():
    emit.DRY = True
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    work = [("hand", n, cases.ops(n)) for n in cases.ORDER]
    for fam, small in gen.FAMILIES:
        if not small:
            continue
        for i in range(per):
            name = "%s-%d" % (fam, i)
            rng = __import__("random").Random("report|%s|%d" % (fam, i))
            work.append((fam, name, gen.MAKE[fam](rng)))
    truth = {name: model.expect(lines) for _f, name, lines in work}
    print("%d programs: %d enumerated, %d generated\n" % (
        len(work), len(cases.ORDER), len(work) - len(cases.ORDER)), flush=True)

    bad = []
    for build in emit.READINGS:
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
            kind = "case" if caught in cases.CASES else "generated"
            print("   %-22s caught by %-18s (%s)" % (name, caught, kind), flush=True)

    print(flush=True)
    per_family = 45
    for name in SLOW + ("reference",):
        if name == "reference":
            here = lab.tree(lab.TASK / "solution")
        else:
            emit.BUILT.clear()
            if name == "slow-charge":
                emit.slow_charge()
            elif name == "slow-sole":
                emit.slow_sole()
            else:
                emit.slow(name[5:], "")
            files = next(iter(emit.BUILT.values()))
            here = lab.tree(lay(files))
        wrong = [n for _f, n, lines in work if drive(here, lines) != truth[n]]
        spent = whole_set(here, "report", per_family, LIMIT * 6)
        verdict = ("over %d s" % (LIMIT * 6)) if spent is None else (
            spent if isinstance(spent, str) else "%.0f s" % spent)
        print("   %-12s %s on the small set; whole graded set (per=%d): %s (limit %d s)"
              % (name, "exact" if not wrong else "WRONG on %s" % wrong[:2], per_family,
                 verdict, LIMIT), flush=True)

    print(flush=True)
    emit.BUILT.clear()
    emit.forge()
    files = emit.BUILT["forge-frozen"]
    here = lab.tree(lay(files))
    hand_bad = [n for n in cases.ORDER if drive(here, cases.ops(n)) != truth[n]]
    seen_bad = [n for _f, n, lines in work
                if n not in cases.CASES and drive(here, lines) != truth[n]]
    print("   %-22s reproduces %d of %d enumerated, fails %d of %d generated"
          % ("forge-frozen", len(cases.ORDER) - len(hand_bad), len(cases.ORDER),
             len(seen_bad), len(work) - len(cases.ORDER)), flush=True)
    if hand_bad or not seen_bad:
        bad.append("forge-frozen")

    print("\n   %d isolation probes are graded by the container run only: %s"
          % (len(PROBES), ", ".join(PROBES)), flush=True)
    print("\n%s" % ("every semantic cheat is caught by a named program"
                    if not bad else "NOT CAUGHT: %s" % bad), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
