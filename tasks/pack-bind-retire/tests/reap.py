"""Kill whatever the run left behind.

A submission can double-fork out of its own session and keep writing after the runner has
returned. /proc is walked rather than trusting any process table the run could have shaped,
and the uid is read from each entry's status file.
"""
import os
import signal
import sys
import time


def owned(pid, uid):
    try:
        with open("/proc/%d/status" % pid, "r", encoding="ascii", errors="replace") as fh:
            for ln in fh:
                if ln.startswith("Uid:"):
                    return int(ln.split()[1]) == uid
    except (IOError, OSError, ValueError, IndexError):
        return False
    return False


def sweep(uid):
    hit = []
    for e in sorted(os.listdir("/proc")):
        if not e.isdigit():
            continue
        pid = int(e)
        if pid == os.getpid() or not owned(pid, uid):
            continue
        hit.append(pid)
    return hit


def main(argv):
    uid = int(argv[0])
    killed = 0
    for sig in (signal.SIGTERM, signal.SIGKILL):
        left = sweep(uid)
        if not left:
            break
        for pid in left:
            try:
                os.kill(pid, sig)
                killed += 1
            except OSError:
                pass
        time.sleep(0.4)
    left = sweep(uid)
    print("reaped uid %d: signalled %d, %d still up" % (uid, killed, len(left)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
