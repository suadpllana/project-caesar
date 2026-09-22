"""Nothing owned by the sandbox user outlives the call that ran it.

The worker gets its own session and a wall clock, and a double fork steps outside both. What
is left behind after the call returns is therefore invisible to `timeout` and to `setsid`, and
the shape that matters is the one that waits for grading to end and then writes a reward.

Ownership is what still holds. This container runs nothing else as uid 1002, so the owner of
/proc/<pid> is a complete answer to "did this come from the submission", and every such pid is
killed here before the grader reads a byte.

None of this is the first line of defence. `/logs/verifier` is root-owned and 0700 from before
the first submitted statement ran, so a survivor cannot write the reward at all. What reaping
closes is the rest of what a survivor could still be doing while grading is in progress.
"""
import os
import signal

SANDBOX_UID = 1002


def owned_pids():
    """Every live pid whose /proc entry belongs to the sandbox user, this process aside."""
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == os.getpid():
            continue
        try:
            if entry.stat().st_uid != SANDBOX_UID:
                continue
        except OSError:
            continue
        yield pid


def main():
    gone = 0
    for pid in owned_pids():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        gone += 1
    print("survivors killed: %d" % gone)


if __name__ == "__main__":
    main()
