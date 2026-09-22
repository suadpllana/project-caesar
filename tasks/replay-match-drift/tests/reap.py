"""Stage one is over: nothing owned by the sandbox uid is allowed to outlive it.

A process that double forks leaves both the session the worker was started in and the wall
clock that bounded it, so when the call returns neither says anything about what is still
alive. The shape that matters is a survivor that waits for grading to end and then writes a
reward, and the thing that still holds against it is ownership: this container runs nothing
else as that uid, so the uid is a complete test for "came out of the submission".

This is the second lock and not the first. The reward directory is root-owned and 0700
before a submitted line runs, so a survivor cannot write it at all; reaping closes off
everything else it could still be doing while stage two reads the record.
"""
import os
import signal
import sys

UID = 1002


def owned():
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        if int(entry.name) == os.getpid():
            continue
        try:
            if entry.stat().st_uid == UID:
                yield int(entry.name)
        except OSError:
            continue


def main():
    gone = 0
    for pid in owned():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        gone += 1
    sys.stdout.write("reaped %d\n" % gone)


if __name__ == "__main__":
    main()
