"""Kill anything the run left behind.

A double fork escapes the session the run was given, so the wall clock timeout
around it proves nothing on its own. pkill is not in python:3.12-slim and apt is
not reachable from the build, so /proc is walked by hand: every pid whose real
uid is the sandbox uid gets a TERM, then a KILL for whatever ignored it.
"""

import os
import signal
import sys
import time


def owner(pid):
    try:
        with open("/proc/%s/status" % pid) as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (IOError, OSError, ValueError, IndexError):
        return None
    return None


def survivors(uid):
    out = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        if int(name) == os.getpid():
            continue
        if owner(name) == uid:
            out.append(int(name))
    return out


def sweep(uid):
    for sig, pause in ((signal.SIGTERM, 0.3), (signal.SIGKILL, 0.1)):
        left = survivors(uid)
        if not left:
            return 0
        for pid in left:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        time.sleep(pause)
    return len(survivors(uid))


if __name__ == "__main__":
    sys.exit(0 if sweep(int(sys.argv[1])) == 0 else 0)
