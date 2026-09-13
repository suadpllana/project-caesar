"""Kill anything still running as the sandbox uid once the worker call has returned.

The worker gets its own session and a wall clock, and a process that forks twice walks out of
both, so neither is evidence about what is still alive. Ownership is: this container runs
nothing else as uid 1002, so any process still holding it came from the submission, and the
shape that matters is the one waiting for grading to finish before it writes a reward. The
reward channel was made root-only before any of that ran; this closes the other half.

The owner of a process is read from its /proc entry's own owner rather than by parsing status
lines, which is one stat call and cannot be confused by a process that exits mid-read.
"""
import os
import signal

SANDBOX = 1002


def survivors():
    mine = os.getpid()
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit() or int(entry.name) == mine:
            continue
        try:
            if entry.stat().st_uid == SANDBOX:
                yield int(entry.name)
        except OSError:
            continue


def main():
    killed = 0
    for pid in list(survivors()):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        killed += 1
    print("reaped %d" % killed)


if __name__ == "__main__":
    main()
