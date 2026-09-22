"""Kill every process still owned by the sandbox uid once the worker call has returned.

The worker runs in its own session under the clock, but a double fork leaves both, and a
process that outlives the worker is exactly the one that waits for grading to finish and then
tries to write a verdict. Nothing else in this container runs as the sandbox uid, so owning
uid alone identifies what the submission started. The reward directory was locked 0700 before
any submitted line ran, so this is the second lock rather than the first.
"""
import os
import signal

SANDBOX = 1002


def owned():
    me = os.getpid()
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit() or int(entry.name) == me:
            continue
        try:
            if entry.stat().st_uid == SANDBOX:
                yield int(entry.name)
        except OSError:
            continue


def main():
    n = 0
    for pid in list(owned()):
        try:
            os.kill(pid, signal.SIGKILL)
            n += 1
        except OSError:
            pass
    print("reaped %d sandbox processes" % n)


if __name__ == "__main__":
    main()
