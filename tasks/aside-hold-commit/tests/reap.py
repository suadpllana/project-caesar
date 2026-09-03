"""Kill anything the run left behind, before a single byte of its report is read.

A probe that double-forks outlives the process the entry point waited on, and a survivor
still holding a descriptor into the work directory would be writing while the grader reads.
`pkill` is not in python:3.12-slim and apt is out of reach from the build, so the process
table is read straight out of /proc. Two passes: collect first, then signal, then confirm,
because signalling while walking the directory races with the walk.
"""

import os
import signal
import sys
import time


def owner(pid):
    try:
        with open("/proc/%s/status" % pid, "r") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def theirs(uid):
    out = []
    for entry in os.listdir("/proc"):
        if entry.isdigit() and int(entry) != os.getpid() and owner(entry) == uid:
            out.append(int(entry))
    return out


def main():
    uid = int(sys.argv[1]) if len(sys.argv) > 1 else 1002
    left = theirs(uid)
    for pid in left:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    if left:
        time.sleep(0.2)
    still = theirs(uid)
    print("reaped %d, still up %d" % (len(left), len(still)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
