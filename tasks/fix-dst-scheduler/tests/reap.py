"""Kill anything the worker uid left behind.

Agent code can double-fork to outlive the call that made it. Nothing owned by
the worker uid may still be running when the grader starts, so this runs as
root between the two and fails the trial if a survivor will not die.

    python reap.py <uid>
"""

import os
import signal
import sys
import time


def owned(uid):
    out = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            st = os.stat("/proc/" + name)
        except OSError:
            continue
        if st.st_uid == uid and int(name) != os.getpid():
            out.append(int(name))
    return out


def main():
    uid = int(sys.argv[1])
    for pid in owned(uid):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    for _ in range(20):
        left = owned(uid)
        if not left:
            return 0
        time.sleep(0.1)
    sys.stderr.write("survivors: %r\n" % owned(uid))
    return 1


sys.exit(main())
