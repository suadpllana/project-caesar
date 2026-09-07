"""Leave nothing of the run alive, and say so with the exit status.

The worker is started in a session of its own, but a submission can double-fork out of it,
and anything still running while the verdict is decided is a process that might still be
writing. The image carries no pkill, so the process table is read directly: /proc/<pid>/stat
gives the session id in field six, /proc/<pid>/status gives the real uid, and anything
belonging to the sandbox uid outside this process's own session is killed.

A polite signal first, then an unconditional one, then a last look. Survivors are a failure
of the run, not a note in the log: the exit status is non-zero and test.sh refuses the run
on it.
"""

import os
import signal
import sys
import time

GRACE = 0.2
ROUNDS = 4


def owner(pid):
    try:
        with open("/proc/%d/status" % pid, "rb") as fh:
            for line in fh:
                if line.startswith(b"Uid:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def session(pid):
    try:
        with open("/proc/%d/stat" % pid, "rb") as fh:
            body = fh.read()
    except OSError:
        return None
    tail = body.rsplit(b")", 1)[-1].split()
    try:
        return int(tail[3])
    except (IndexError, ValueError):
        return None


def leftovers(uid, mine):
    found = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid == os.getpid() or session(pid) == mine:
            continue
        if owner(pid) == uid:
            found.append(pid)
    return sorted(found)


def strike(pids, how):
    for pid in pids:
        try:
            os.kill(pid, how)
        except OSError:
            pass


def main(argv):
    if len(argv) < 2:
        return 0
    uid = int(argv[1])
    mine = session(os.getpid())
    for turn in range(ROUNDS):
        left = leftovers(uid, mine)
        if not left:
            return 0
        strike(left, signal.SIGTERM if turn == 0 else signal.SIGKILL)
        time.sleep(GRACE)
    left = leftovers(uid, mine)
    if not left:
        return 0
    sys.stderr.write("reap: uid %d still owns %d process(es): %s\n"
                     % (uid, len(left), left))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
