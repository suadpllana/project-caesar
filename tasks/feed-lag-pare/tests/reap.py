"""Whatever the submitted service left behind, swept by owner.

Stage one runs in a session of its own and under a wall clock. A double fork walks out of
both, so once the call has returned neither says anything about what is still alive - and a
process that outlives the call is exactly the shape that waits for grading to finish and then
writes itself a reward. What does still hold is ownership: nothing else in this container runs
as the sandbox user, so holding that uid is a complete test for having come out of the
submission.

This is the second lock rather than the first. The reward channel is a root-owned directory
made 0700 before any submitted line ran, so a survivor cannot reach it either way; sweeping
shuts the remaining doors while the grader reads.
"""
import os
import signal

SANDBOX = 1002


def survivors():
    """Every live pid owned by the sandbox user, read off the owner of its /proc entry."""
    mine = os.getpid()
    for item in os.scandir("/proc"):
        if not item.name.isdigit() or int(item.name) == mine:
            continue
        try:
            owner = item.stat().st_uid
        except OSError:
            continue
        if owner == SANDBOX:
            yield int(item.name)


def main():
    swept = 0
    for pid in survivors():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        swept += 1
    print("swept %d survivor(s)" % swept)


if __name__ == "__main__":
    main()
