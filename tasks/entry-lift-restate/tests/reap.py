"""Clear out anything still alive under the sandbox uid once the worker call has returned.

The worker runs in a session of its own with a wall clock over it. A double fork leaves both
behind, so when the call returns neither the session nor the clock tells us what is still
running - and a survivor that waits for grading to end and then writes a reward is exactly
the shape this has to shut down. Ownership is the one thing that still holds: the sandbox uid
belongs to nothing else in this container, so the owner of /proc/<pid> is a complete test for
"this came out of the submission".

This is the outer lock rather than the inner one. The reward lives in a root-owned directory
made 0700 before a submitted line ran, so a survivor cannot write it in any case. Reaping
closes off everything else a survivor could still be doing while the grader reads.
"""
import os
import signal

SANDBOX_UID = 1002


def owned_by_sandbox():
    """Live pids whose /proc entry belongs to the sandbox uid."""
    mine = os.getpid()
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit() or int(entry.name) == mine:
            continue
        try:
            if entry.stat().st_uid == SANDBOX_UID:
                yield int(entry.name)
        except OSError:
            continue


def main():
    gone = 0
    for pid in owned_by_sandbox():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        gone += 1
    print("survivors killed: %d" % gone)


if __name__ == "__main__":
    main()
