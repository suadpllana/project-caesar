"""Close the door on anything half one left running.

Half one is started in a session of its own under a wall clock, but a process that forks twice
leaves both behind, and the shape that matters is a survivor that waits for grading to finish
and then writes a reward. The reward channel is already a root-owned directory at mode 0700
from before the first submitted line ran, so a survivor cannot write it; this shuts down
everything else it could still be doing while half two reads.

Ownership is the test. No other process in this container runs as the sandbox uid, so a
process that does came from the submission.
"""
import os
import signal

PEN = 1002


def theirs():
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == os.getpid():
            continue
        try:
            if entry.stat().st_uid == PEN:
                yield pid
        except OSError:
            continue


def main():
    shut = 0
    for pid in theirs():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        shut += 1
    print("sandbox processes shut down: %d" % shut)


if __name__ == "__main__":
    main()
