"""Kill anything the run left behind under the sandbox uid.

A double fork escapes the process group, so `setsid --wait` returning is not evidence that
the run has finished. This walks /proc and signals every process whose owner is the uid the
run dropped to. Ownership is taken from stat() on the /proc entry itself rather than from
parsing status text, because the directory's owner is the process's real uid and needs no
parsing to be sure of.

Nothing here trusts the process list to be stable: entries vanish between listing and
signalling, so every syscall is guarded and a vanished pid counts as reaped.
"""

import os
import signal
import sys
import time


def mine(pid, uid):
    try:
        return os.stat("/proc/%d" % pid).st_uid == uid
    except OSError:
        return False


def live(uid):
    out = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid != os.getpid() and mine(pid, uid):
            out.append(pid)
    return out


def swing(pids, sig):
    for pid in pids:
        try:
            os.kill(pid, sig)
        except OSError:
            pass


def main(argv):
    uid = int(argv[1]) if len(argv) > 1 else 1002
    left = live(uid)
    if not left:
        return 0
    swing(left, signal.SIGKILL)
    for _ in range(20):
        left = live(uid)
        if not left:
            return 0
        time.sleep(0.1)
        swing(left, signal.SIGKILL)
    sys.stderr.write("[reap] still up under uid %d: %r\n" % (uid, live(uid)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
