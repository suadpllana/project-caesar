"""The plausible-but-wrong readings, for tools/readingcheck.py.

Per-rule coverage on paper is not coverage. The question is whether a SPECIFIC wrong
reading survives the whole enumerated set, and the only way to know is to write that
reading down and run it. A reading the set does not separate is one a probe agent can hold
while passing every hand-written case, dying on a handful of generated journals - which
under all-or-nothing grading is indistinguishable from bad luck.

The readings are taken from the shipped single-mistake cheats rather than written again
here, by pulling the file bodies straight out of cheat/*.sh. That is deliberate: two hand
copies of the same wrong reading drift, and the thing that must be separated is the reading
the cheat suite actually ships.
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402

REFERENCE = str(ROOT / "solution")

BODY = re.compile(r'cat > "\$APP/pol/(\S+?)" <<\'GSO_EOF\'\n(.*?)\nGSO_EOF', re.S)

# Probes and tampers are not readings of the rules - they are attacks on the reward
# channel and on the attestations, and they are graded by different tests.
NOT_A_READING = ("answer-key", "reward-daemon", "plant-run-output", "plant-and-exit",
                 "probe-privileges", "read-answers", "sweep-environment",
                 "rewrite-kernel", "patch-emitter", "kill-monitor",
                 "quiet-monitor", "swap-kernel")


def harvest():
    out = {}
    for path in sorted((ROOT / "cheat").glob("cheat-*.sh")):
        name = path.stem[len("cheat-"):]
        if name in NOT_A_READING:
            continue
        files = dict(BODY.findall(path.read_text()))
        if files:
            out[name] = files
    return out


READINGS = harvest()


def run(policy, text):
    return harness.run(text, policy)


def enumerated():
    return [(n, cases.PROGS[n]) for n in sorted(cases.PROGS)]


def generated(n):
    return [("g%04d" % i, gen.text("reading/%d" % i)) for i in range(n)]
