"""What catches each cheat, and at which layer.

A cheat scoring 0 is not evidence on its own: a probe can score 0 because it stopped working
after the first program, and a wrong reading can score 0 because the enumerated set happens to
crash it rather than because the rule it breaks is tested. So this asserts the layer, never just
the reward: for a reading, which enumerated case fails it; for the forgery, that it passes every
enumerated case and fails the programs it could not have seen; for the two right-but-slow
services, the time against the stated limit.

The isolation probes are not measured here. They attack the verifier's own machinery and can only
be judged in the container, by tools/docker_trial.py.

    python3 authoring/queue-hold-drop/cheat_report.py [--slow]
"""
import pathlib
import random
import re
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "tasks/queue-hold-drop/tests"))
sys.path.insert(0, str(HERE.parents[1] / "tasks/queue-hold-drop/tests/seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402

CHEAT = lab.TASK / "cheat"
LIMIT = 60.0
PROBES = ("probe-",)


def files(path):
    out = {}
    text = path.read_text(encoding="utf-8")
    for m in re.finditer(r"cat > /app/pend/(\S+) <<'PYEOF'\n(.*?)\nPYEOF\n", text, re.S):
        out[m.group(1)] = m.group(2) + "\n"
    return out


def tree_for(path):
    here = lab.tree(lab.TASK / "solution")
    for name, src in files(path).items():
        (here / "pend" / name).write_text(src, encoding="utf-8", newline="\n")
    return here


def drive(here, lines):
    try:
        return lab.drive(here, lines)
    except Exception as exc:
        return ["RAISED", type(exc).__name__, str(exc)[:80]]


def nonce(n=int(next((a.split("=")[1] for a in sys.argv if a.startswith("--n=")), 40))):
    out = []
    small = [fam for fam, big in gen.FAMILIES if not big]
    for i in range(n):
        fam = small[i % len(small)]
        r = random.Random("cheatnonce|%s|%d" % (fam, i))
        out.append(("%s-%d" % (fam, i), gen.build(fam, r, small=True)))
    return out


def main():
    want_slow = "--slow" in sys.argv
    hand = [(name, cases.ops(name), model.expect(cases.ops(name))) for name in cases.ORDER]
    later = [(name, lines, model.expect(lines)) for name, lines in nonce()]
    bad = 0
    for path in sorted(CHEAT.glob("cheat-*.sh")):
        tag = path.stem[len("cheat-"):]
        if tag.startswith(PROBES):
            print("%-20s probe: judged in the container only" % tag)
            continue
        here = tree_for(path)
        if tag.startswith("slow-"):
            if not want_slow:
                print("%-20s right and slow: rerun with --slow to time it" % tag)
                continue
            spent = 0.0
            for fam in ("wide", "deep"):
                lines = gen.build(fam, random.Random("cheat|%s" % fam), small=False)
                t0 = time.time()
                got = drive(here, lines)
                spent += time.time() - t0
                if got != model.expect(lines):
                    print("%-20s SLOW CHEAT IS ALSO WRONG on %s" % (tag, fam))
                    bad += 1
            mark = "over" if spent > LIMIT else "UNDER"
            print("%-20s %s the limit: %.1f s on two of the six scale programs (limit %.0f)"
                  % (tag, mark, spent, LIMIT))
            if spent <= LIMIT:
                bad += 1
            continue
        caught = [name for name, lines, want in hand if drive(here, lines) != want]
        missed = [name for name, lines, want in later if drive(here, lines) != want]
        if tag == "forge-from-truth":
            if caught:
                print("%-20s FORGERY FAILS %d enumerated programs (%s)"
                      % (tag, len(caught), caught[:3]))
                bad += 1
            elif not missed:
                print("%-20s FORGERY SURVIVES the generated programs" % tag)
                bad += 1
            else:
                print("%-20s replays all %d enumerated, wrong on %d of %d generated"
                      % (tag, len(hand), len(missed), len(later)))
            continue
        if not caught:
            print("%-20s NOT CAUGHT by any enumerated case" % tag)
            bad += 1
        else:
            print("%-20s caught by %s (%d of %d enumerated, %d of %d generated)"
                  % (tag, caught[0], len(caught), len(hand), len(missed), len(later)))
    print("%d findings" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
