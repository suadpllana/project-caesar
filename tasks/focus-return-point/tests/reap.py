"""Stop every process still owned by the run's uid before grading begins.

A submission can double-fork and leave something alive past the runner's exit, which
could otherwise still be writing while the verdict is decided. The verifier image has
no pkill, so this walks /proc/*/status for the Uid line and sends SIGKILL, up to three
passes, then reports what survived.
"""

import os
import signal
import sys
import time


def belongs(pid, uid):
    try:
        with open("/proc/%d/status" % pid) as fh:
            for line in fh:
                if line[:4] == "Uid:":
                    return int(line.split()[1]) == uid
    except (OSError, ValueError, IndexError):
        pass
    return False


def survivors(uid):
    mine = os.getpid()
    out = []
    for name in os.listdir("/proc"):
        if name.isdigit() and int(name) != mine and belongs(int(name), uid):
            out.append(int(name))
    return sorted(out)


def main(argv):
    uid = int(argv[1]) if len(argv) > 1 else -1
    if uid < 0:
        return 0
    for _ in range(3):
        left = survivors(uid)
        if not left:
            return 0
        for pid in left:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        time.sleep(0.25)
    left = survivors(uid)
    if left:
        sys.stderr.write("reap: %d processes of uid %d survived\n" % (len(left), uid))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
