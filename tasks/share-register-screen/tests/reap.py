"""Kill anything the graded run left behind.

The run is a session of its own under an unprivileged uid, but a process that double forks
outlives the session leader, and pkill is not in the base image. This walks /proc, which
needs nothing installed, and signals every process owned by that uid other than this one.
"""

from __future__ import annotations

import os
import sys
import time


def owners(uid):
    out = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid == os.getpid():
            continue
        try:
            if os.stat("/proc/%d" % pid).st_uid == uid:
                out.append(pid)
        except OSError:
            continue
    return out


def main(argv):
    uid = int(argv[1]) if len(argv) > 1 else 1002
    for sig, pause in ((15, 0.4), (9, 0.2), (9, 0.0)):
        left = owners(uid)
        if not left:
            break
        for pid in left:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        if pause:
            time.sleep(pause)
    left = owners(uid)
    sys.stderr.write("reap: %d left\n" % len(left))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
