"""Kill whatever the submission left running, before the grader reads anything.

The worker is started in its own session under a wall clock, and a double fork walks out of
both: when the call returns, neither the session nor the clock says anything about what is
still alive. A survivor is exactly the shape that waits for grading to finish and then
writes a reward, so it goes now.

Ownership is the test that still holds. Nothing else in this container runs as the sandbox
uid, so a process owned by it came from the submission and from nowhere else. The uid is
read out of /proc/<pid>/status rather than off the directory, because a process that has
changed its own credentials is exactly the one worth catching.

This is the second lock, not the first. The reward channel is a root-owned directory made
0700 before a submitted line ran, so a survivor cannot write it in any case; reaping shuts
the door on everything else it could still be doing while the grader reads.
"""
import os
import signal
import time

SANDBOX_UID = 1002


def uid_of(pid):
    """The real uid of a live process, or None if it is gone or unreadable."""
    try:
        with open("/proc/%d/status" % pid, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def survivors():
    mine = os.getpid()
    found = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        pid = int(name)
        if pid == mine:
            continue
        if uid_of(pid) == SANDBOX_UID:
            found.append(pid)
    return found


def main():
    killed = 0
    for pid in survivors():
        try:
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except OSError:
            continue
    # A second pass, because a survivor can fork while the first one is walking /proc.
    if killed:
        time.sleep(0.2)
        for pid in survivors():
            try:
                os.kill(pid, signal.SIGKILL)
                killed += 1
            except OSError:
                continue
    print("survivors killed: %d" % killed)


if __name__ == "__main__":
    main()
