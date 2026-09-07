"""Clear out anything the submitted binder left running.

The worker is started in its own session, but a double fork leaves that session behind, so
killing the process group is not enough. Ownership is what survives the fork: every process
still running as the sandbox uid once the worker has returned is a survivor, and a survivor is
exactly the thing that would try to write a reward once grading is over. The reward channel is
root-owned and already locked by then, so this only closes the other half - but it closes it
before pytest starts rather than after.

A /proc entry is owned by the uid the process runs as, so os.stat on the directory answers the
question without parsing anything.
"""
import os
import signal

SANDBOX_UID = 1002


def owned_by(uid):
    mine = os.getpid()
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == mine:
            continue
        try:
            if entry.stat().st_uid == uid:
                yield pid
        except OSError:
            continue


def main():
    killed = 0
    for pid in sorted(owned_by(SANDBOX_UID)):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        killed += 1
    print("reaped %d survivor(s)" % killed)


if __name__ == "__main__":
    main()
