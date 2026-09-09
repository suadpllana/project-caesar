"""Time one program of one family under one host, with a cap.

The correct-but-slow readings are minutes apiece on a single graded program, so the honest
measurement is one program against the limit for the whole set rather than a full sweep.

    python3 time_one.py <solution-dir|reading-name> <family> [cap seconds]
"""
import pathlib
import signal
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TESTS = HERE.parents[1] / "tasks" / "publish-settle-order" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import gen  # noqa: E402
import lab  # noqa: E402
import mkoverlay  # noqa: E402

CAP = int(sys.argv[3]) if len(sys.argv) > 3 else 300


def bail(_sig, _frm):
    raise TimeoutError


where = sys.argv[1]
fam = sys.argv[2]
policy = pathlib.Path(where)
if policy.name != "solution":
    policy = mkoverlay.build(HERE / "readings" / policy.name)
lb = lab.Lab(policy)
prog = next(p for p in gen.programs("deadbeef", 45) if p[0] == fam)
signal.signal(signal.SIGALRM, bail)
signal.alarm(CAP)
t = time.time()
try:
    lb.run(prog[2])
    print("%-22s %-5s %7.1fs" % (pathlib.Path(where).name, fam, time.time() - t), flush=True)
except TimeoutError:
    print("%-22s %-5s  over %ds" % (pathlib.Path(where).name, fam, CAP), flush=True)
signal.alarm(0)
lb.close()
