"""Kill anything the run left behind, before grading reads its report.

Agent code can double-fork to outlive the call that ran it. The reward channel is
root-owned and locked, so a survivor cannot write it, but a survivor holding the report
descriptor could still rewrite the file the grader is about to read. Nothing owned by the
run's uid is allowed to be alive when this returns.
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
            if os.stat(os.path.join("/proc", name)).st_uid != uid:
                continue
        except OSError:
            continue
        out.append(int(name))
    return out


def main(argv):
    uid = int(argv[1]) if len(argv) > 1 else 1002
    for sig in (signal.SIGTERM, signal.SIGKILL):
        left = owned(uid)
        if not left:
            break
        for pid in left:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        time.sleep(0.4)
    left = owned(uid)
    if left:
        print("survivors: %s" % left)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
