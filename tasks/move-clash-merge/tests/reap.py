"""Leave no process of the run's uid alive when the grading starts.

A submission can double-fork, so something it started can outlive the runner and still be
writing while the verdict is decided. The verifier image has no pkill, so the process table is
read straight out of /proc: every entry whose real uid matches is signalled, politely once and
then not, and the pass repeats while anything is still there. A uid with survivors after that
is reported by the exit status, which `test.sh` treats as a failed run.
"""

import os
import signal
import sys
import time

PASSES = 4
PAUSE = 0.2


def owner(pid):
    """The real uid of a process, or None if it has gone or cannot be read."""
    try:
        with open("/proc/%d/status" % pid, encoding="ascii", errors="replace") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def theirs(uid):
    mine = os.getpid()
    return sorted(pid for pid in (int(n) for n in os.listdir("/proc") if n.isdigit())
                  if pid != mine and owner(pid) == uid)


def main(argv):
    if len(argv) < 2:
        return 0
    uid = int(argv[1])
    if uid < 0:
        return 0
    left = theirs(uid)
    for attempt in range(PASSES):
        if not left:
            return 0
        sig = signal.SIGTERM if attempt == 0 else signal.SIGKILL
        for pid in left:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        time.sleep(PAUSE)
        left = theirs(uid)
    sys.stderr.write("reap: uid %d still owns %d process(es): %s\n"
                     % (uid, len(left), left[:8]))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
