"""Kill anything still owned by the run's uid before the verdict is decided.

A submission can double-fork and leave a process alive past the runner's exit; the reward
file is already root-owned inside a 700 directory, but a survivor writing into the work
tree while the grader reads it would still be noise in the verdict. The verifier image has
no pkill, so this reads the Uid line of every /proc entry and sends SIGKILL. Exit status is
non-zero only if something is still there after three passes, which the entry point treats
as a failed run.
"""

import os
import signal
import sys
import time

STATUS = "/proc/%d/status"


def owner(pid):
    try:
        with open(STATUS % pid) as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def alive(uid):
    me = os.getpid()
    found = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid != me and owner(pid) == uid:
            found.append(pid)
    return sorted(found)


def main(argv):
    if len(argv) < 2:
        return 0
    uid = int(argv[1])
    if uid < 0:
        return 0
    for attempt in range(3):
        left = alive(uid)
        if not left:
            return 0
        for pid in left:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        time.sleep(0.2 * (attempt + 1))
    left = alive(uid)
    if left:
        sys.stderr.write("sweepup: %d processes of uid %d would not die\n" % (len(left), uid))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
