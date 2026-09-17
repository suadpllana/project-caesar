"""Kill whatever the submission left running, identified by the uid it ran as.

The worker is given its own session and a wall clock, and a double fork walks out of both, so
neither says anything once the call has returned. The uid does: nothing else in this container
runs as the sandbox user, so a live process still holding it is a survivor of the stage that
executed agent code, and a survivor is exactly the shape that waits for grading to finish and
then writes itself a reward. That door is already locked - the channel is root-owned and was
sealed before any of this ran - and this shuts the one beside it.
"""
import os
import signal

SANDBOX = 1002


def survivors():
    """Every live pid owned by the sandbox uid, youngest first."""
    found = []
    for entry in sorted(os.listdir("/proc"), reverse=True):
        if not entry.isdigit():
            continue
        try:
            if os.stat("/proc/" + entry).st_uid == SANDBOX:
                found.append(int(entry))
        except OSError:
            continue
    return found


def main():
    mine = os.getpid()
    killed = 0
    for pid in survivors():
        if pid == mine:
            continue
        for target, how in ((-pid, "group"), (pid, "process")):
            try:
                os.kill(target, signal.SIGKILL)
                killed += 1
                break
            except OSError:
                continue
    print("reaped %d" % killed)


if __name__ == "__main__":
    main()
