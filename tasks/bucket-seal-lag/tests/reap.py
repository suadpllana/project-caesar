"""Kill whatever the run left behind before anything is read.

`pkill` is absent from python:3.12-slim and apt cannot be reached from the build,
so this reads /proc directly. It earns its place because a probe that double-forks
outlives the process the runner waited on, and a survivor still holding a
descriptor into /work would be writing while the grader reads.
"""

import os
import signal
import sys


def mine(entry, uid):
    try:
        with open("/proc/%s/status" % entry) as fh:
            for line in fh:
                if not line.startswith("Uid:"):
                    continue
                return int(line.split()[1]) == uid
    except (IOError, OSError, IndexError, ValueError):
        pass
    return False


def main(argv):
    uid = int(argv[1]) if len(argv) > 1 else 1002
    self = os.getpid()
    struck = 0
    for entry in sorted(os.listdir("/proc")):
        if not entry.isdigit():
            continue
        if int(entry) == self or not mine(entry, uid):
            continue
        try:
            os.kill(int(entry), signal.SIGKILL)
        except OSError:
            continue
        struck += 1
    sys.stderr.write("reaped %d\n" % struck)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
