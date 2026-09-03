"""Kill whatever the run left running.

A submission can double-fork so that something outlives the call that started it, and a
survivor holding the run's uid is a process that could still be writing when grading
begins. The base image has no pkill and apt cannot be reached from here, so this reads
/proc directly.

The owner of a process is taken from the owner of its /proc entry, which the kernel sets
to the real uid, so no file inside it has to be parsed.
"""

import os
import signal
import sys

PROC = "/proc"


def owned_by(uid):
    for entry in os.scandir(PROC):
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat(follow_symlinks=False).st_uid == uid:
                yield int(entry.name)
        except OSError:
            continue


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: reap.py <uid>\n")
        return 2
    uid = int(argv[1])
    self_pid = os.getpid()
    doomed = [pid for pid in owned_by(uid) if pid != self_pid]
    for pid in doomed:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
    if doomed:
        sys.stderr.write("[reap] %d survivor(s) of uid %d killed: %r\n"
                         % (len(doomed), uid, doomed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
