"""Kill anything still running as the sandbox user when the worker call returns.

The worker is started in its own session under a wall clock. A double fork walks out of both,
so when the call returns neither the session nor the clock says anything about what is still
alive - and a survivor is exactly the shape that waits for grading to finish and then writes a
reward. Ownership is the thing that still holds: no other process in this container runs as the
sandbox uid, so uid is a complete test for "came from the submission".

This is the second lock, not the first. The reward channel is a root-owned directory made 0700
before any submitted line ran, so a survivor cannot write it in the first place. Reaping shuts
the door on everything else a survivor could still be doing while the grader reads.
"""
import os
import signal

SANDBOX_UID = 1002


def sandbox_pids():
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == os.getpid():
            continue
        try:
            if entry.stat().st_uid == SANDBOX_UID:
                yield pid
        except OSError:
            continue


def main():
    killed = 0
    for pid in sandbox_pids():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        killed += 1
    print("survivors killed: %d" % killed)


if __name__ == "__main__":
    main()
