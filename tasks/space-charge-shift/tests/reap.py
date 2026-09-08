"""Kill whatever the submitted layer left behind, and say how much there was.

The worker runs in its own session, but a double fork escapes a process group, so ownership is
the only reliable sweep: once the worker has returned, any process still running as the sandbox
uid is a survivor, and a survivor is exactly what would try to write a reward after grading is
over. The reward channel is root-owned and locked by then, which closes the other half.

The uid comes from the owner of /proc/<pid>, which the kernel sets to the process owner, so no
parsing of status files is involved.
"""
import os
import signal

SANDBOX = 1002


def owned_by(pid, uid):
    try:
        return os.stat("/proc/%d" % pid).st_uid == uid
    except OSError:
        return False


def sweep(uid, me):
    left = []
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid != me and owned_by(pid, uid):
            left.append(pid)
    return sorted(left)


def main():
    gone = 0
    for pid in sweep(SANDBOX, os.getpid()):
        try:
            os.kill(pid, signal.SIGKILL)
            gone += 1
        except OSError:
            pass
    print("survivors killed: %d" % gone)


if __name__ == "__main__":
    main()
