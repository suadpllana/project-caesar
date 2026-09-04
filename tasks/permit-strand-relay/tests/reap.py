"""Nothing the unprivileged run started may still be alive when grading starts.

pkill is absent from the slim image and the build cannot reach apt, so the
process table is read straight out of /proc. A double-forked child that
outlived its session is exactly what this is for.
"""

import os
import signal
import sys


def under(uid):
    found = []
    for leaf in sorted(os.listdir("/proc")):
        if not leaf.isdigit():
            continue
        try:
            with open(os.path.join("/proc", leaf, "status")) as fh:
                for line in fh:
                    if line.startswith("Uid:"):
                        if int(line.split()[1]) == uid:
                            found.append(int(leaf))
                        break
        except OSError:
            continue
    return found


def main():
    want = int(sys.argv[1])
    self = os.getpid()
    for pid in under(want):
        if pid != self:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass


if __name__ == "__main__":
    main()
