"""The host emulation, tied together in one command.

Real tree, real book, real streams, real sealed model. It does NOT cover the privilege drop,
the root-owned reward channel, the root-only ground truth or the process teardown, and it
cannot: those live in the two-image trial, tools/docker_trial2.py. Anything reported from
here has to say which half it measured.

    python3 authoring/trial.py [generated-count]
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def step(name, args):
    print("\n== %s" % name)
    r = subprocess.run([sys.executable, str(HERE / args[0])] + args[1:], text=True)
    return r.returncode


def main(argv):
    n = argv[1] if len(argv) > 1 else "150"
    bad = 0
    bad += step("the reference against the sealed model", ["fuzz.py", n])
    bad += step("alternative correct implementations", ["variant_check.py", n])
    bad += step("names and scan order", ["tiecheck.py", n])
    bad += step("the cheat suite", ["cheat_report.py", n])
    print("\n%s" % ("everything the host can measure is clean" if bad == 0
                    else "%d steps failed" % bad))
    print("not covered here: the privilege drop, the reward channel, the root-only ground")
    print("truth, the teardown. Those are tools/docker_trial2.py.")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
