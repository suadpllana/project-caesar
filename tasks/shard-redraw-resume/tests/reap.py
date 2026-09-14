"""Kill whatever the submitted driver left running, identified by the uid it had to run under.

A wall clock and a session of its own bound the worker, and a double fork steps out of both, so
once the call returns neither is evidence that nothing survived. The uid is: no other process in
this container runs as the sandbox user, so one still holding it is a survivor, and a survivor
is exactly the shape that waits for grading to finish and then writes itself a reward. The
reward channel is root-owned and was locked before any of this ran; this closes the other door.

Printed counts go to the trial log. Nothing here decides the reward.
"""
import os
import signal

SANDBOX = 1002


def live():
    """Every pid currently visible, as integers."""
    for entry in os.scandir("/proc"):
        if entry.name.isdigit():
            yield int(entry.name)


def uid_of(pid):
    """The real uid of a process, or None when it went away while we were looking."""
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    field = line.split()
                    if len(field) > 1 and field[1].isdigit():
                        return int(field[1])
                    return None
    except OSError:
        return None
    return None


def main():
    mine = os.getpid()
    killed = 0
    for pid in live():
        if pid == mine or uid_of(pid) != SANDBOX:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        killed += 1
    print("reaped %d survivor(s)" % killed)


if __name__ == "__main__":
    main()
