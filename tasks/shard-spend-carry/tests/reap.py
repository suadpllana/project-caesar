"""Anything the submitted engine left running, killed by owner.

The worker is given a session of its own and a wall clock, and a double fork leaves both
behind, so neither proves anything once the call has returned. The uid does: nothing else in
this container runs as the sandbox user, so a live process still holding it is a survivor, and
a survivor is exactly the shape that waits for grading to end and then writes itself a reward.
The reward channel is root-owned and was locked before any of this started; this shuts the
other door.

Ownership is read off the /proc entry itself rather than parsed out of its status file: the
directory belongs to the real uid of the process, and a process that exits while it is being
looked at simply stops existing.
"""
import os
import signal

SANDBOX = 1002


def survivors():
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == os.getpid():
            continue
        try:
            if entry.stat().st_uid == SANDBOX:
                yield pid
        except OSError:
            continue


def main():
    gone = 0
    for pid in list(survivors()):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        gone += 1
    print("reaped %d" % gone)


if __name__ == "__main__":
    main()
