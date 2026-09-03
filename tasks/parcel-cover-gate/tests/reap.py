"""Nothing the run left behind may be alive while the rows are being read.

A child that double-forks out of its session goes on running after the wall
clock has taken its parent down, and it can still be writing when grading
starts. `pkill` is not in python:3.12-slim and there is no apt layer here, so
this reads /proc directly.

Two rounds. The first asks. The second does not, and anything still there after
it is beyond what a verifier can do about it.
"""

import errno
import os
import signal
import sys
import time

PROC = "/proc"


def theirs(uid):
    """Every live pid owned by that uid, this process excluded."""
    mine = os.getpid()
    for entry in os.listdir(PROC):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid == mine:
            continue
        try:
            if os.stat(os.path.join(PROC, entry)).st_uid == uid:
                yield pid
        except OSError as why:
            if why.errno not in (errno.ENOENT, errno.EACCES, errno.ESRCH):
                raise


def sweep(uid, sig):
    hit = 0
    for pid in theirs(uid):
        try:
            os.kill(pid, sig)
            hit += 1
        except OSError:
            pass
    return hit


def main(argv):
    uid = int(argv[1]) if len(argv) > 1 else 1002
    for sig, wait in ((signal.SIGTERM, 0.4), (signal.SIGKILL, 0.2)):
        if not sweep(uid, sig):
            break
        time.sleep(wait)
    left = list(theirs(uid))
    if left:
        sys.stderr.write("uid %d still has %d process(es): %r\n"
                         % (uid, len(left), left[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
