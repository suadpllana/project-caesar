"""Which layer catches each wrong reading, and how much of the population it moves.

For every reading built by make_readings.py: the hand cases it fails (the one named for it must
be among them), and the share of generated programs whose report it changes, family by family.
A reading that moves nothing is a reading the population does not test, whatever it scores.
The two slow readings are exact; for them the report checks agreement on the small programs and
leaves the wall clock, and the scale families, to host_trial.py. Every other reading is also run on
one flags program, the only family that separates all-groups, under a per-program alarm so a reading
that turns out slow is reported as moved instead of hanging the report.

The forgery is checked from the other side: it must pass every hand case - otherwise it is not a
forgery and proves nothing about the generated population - and fail the generated programs.

Usage: python3 authoring/blank-fill-sure/cheat_report.py [seed] [per]
"""
import json
import os
import shutil
import signal
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tasks", "blank-fill-sure")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import make_readings  # noqa: E402
import model  # noqa: E402
import tree  # noqa: E402

ALARM_SECONDS = 60


class Late(Exception):
    pass


def _late(_sig, _frame):
    raise Late()


def timed(run, text):
    signal.signal(signal.SIGALRM, _late)
    signal.alarm(ALARM_SECONDS)
    try:
        return run(text)
    except Late:
        return "late"
    except Exception:
        return None
    finally:
        signal.alarm(0)


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "report"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    with open(os.path.join(TASK, "tests", "seal", "gt.json"), encoding="utf-8") as fh:
        gt = json.load(fh)
    progs = gen.programs(seed, per)
    small = [p for p in progs if p[0] not in ("wide", "flags")]
    small += [p for p in progs if p[0] == "flags"][:1]
    want = {name: model.expect(lines) for _f, name, lines in small}
    failures = 0
    for name, (belief, case, _patches) in make_readings.READINGS.items():
        run = tree.runner(os.path.join(make_readings.OUT, name))
        hand_bad = []
        for n in cases.ORDER:
            got = timed(run, "\n".join(cases.prog(n)) + "\n")
            if got != gt[n]:
                hand_bad.append(n)
        moved, total, fams = 0, 0, {}
        for fam, n, lines in small:
            if not case and fam == "flags":
                continue
            got = timed(run, "\n".join(lines) + "\n")
            total += 1
            if got != want[n]:
                moved += 1
                fams[fam] = fams.get(fam, 0) + 1
        if case:
            ok = case in hand_bad
            verdict = "caught by %s" % case if ok else "NOT CAUGHT by %s" % case
        else:
            ok = not hand_bad and moved == 0
            verdict = "exact on every small program" if ok else "NOT EXACT"
        failures += not ok
        top = ", ".join("%s %d" % kv for kv in sorted(fams.items(), key=lambda kv: -kv[1])[:3])
        print("%-14s %-34s hand %2d/%d  generated %5.1f%%  (%s)"
              % (name, verdict, len(hand_bad), len(cases.ORDER), 100.0 * moved / total, top))
    failures += forgery(gt, small, want)
    print("%d reading(s) not caught as designed" % failures)
    return 1 if failures else 0


def heredoc(script, path):
    """The file a cheat script writes at `path`, as the quoted heredoc carries it."""
    with open(script, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    start = lines.index("cat > %s <<'PYEOF'" % path) + 1
    return "\n".join(lines[start:lines.index("PYEOF", start)]) + "\n"


def forgery(gt, small, want):
    """The forged answer key must pass every hand case and still fail the generated programs."""
    script = os.path.join(TASK, "cheat", "cheat-forge-hand.sh")
    d = tempfile.mkdtemp(prefix="bfs-forge-")
    for part in ("cmp.py", "join.py"):
        shutil.copy(os.path.join(TASK, "environment", "app_src", "rs", part), d)
    with open(os.path.join(d, "keep.py"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(heredoc(script, "/app/rs/keep.py"))
    run = tree.runner(d)
    hand_bad = [n for n in cases.ORDER if timed(run, "\n".join(cases.prog(n)) + "\n") != gt[n]]
    moved = sum(1 for _f, n, lines in small if timed(run, "\n".join(lines) + "\n") != want[n])
    ok = not hand_bad and moved > 0
    print("%-14s %-34s hand %2d/%d  generated %5.1f%%" % (
        "forge-hand", "passes every hand case, fails generated" if ok else
        "NOT AS DESIGNED (hand failed: %s)" % hand_bad[:3],
        len(hand_bad), len(cases.ORDER), 100.0 * moved / len(small)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
