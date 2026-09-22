"""Reap any process left under the sandbox account once half one has returned.

Half one runs behind `setsid` and a wall clock, so a double fork can leave a descendant alive
after the call returns - the shape to worry about is one that sleeps past the grader and then
writes a reward. That particular move is already dead on arrival, because the reward file lives
in a root-owned 0700 directory sealed before a single submitted line ran. This closes the rest
of the door. Every process the submission could have spawned runs as uid 1002 and nothing else
in this container does, so ownership by that uid is the entire membership test.
"""
import os
import signal
from pathlib import Path

SANDBOX = 1002


def survivors():
    """Pids still owned by the sandbox uid, taken from the owner of each /proc/<pid> entry."""
    me = os.getpid()
    for proc in Path("/proc").glob("[0-9]*"):
        pid = int(proc.name)
        if pid == me:
            continue
        try:
            owner = proc.stat().st_uid
        except OSError:
            continue
        if owner == SANDBOX:
            yield pid


def main():
    reaped = 0
    for pid in survivors():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        reaped += 1
    print("reaped %d sandbox survivor(s)" % reaped)


if __name__ == "__main__":
    main()
