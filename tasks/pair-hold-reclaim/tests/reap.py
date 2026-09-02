"""Kill anything the run left behind before grading starts.

pkill is not in the base image and apt is unreachable from the build, so /proc is walked
directly. A double-forked writer that outlives its session is the thing this exists for.
"""

import os
import signal
import sys


def owned_by(pid, uid):
    try:
        with open("/proc/%s/status" % pid) as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1]) == uid
    except OSError:
        return False
    return False


def main(argv):
    uid = int(argv[1])
    mine = str(os.getpid())
    killed = 0
    for pid in sorted(p for p in os.listdir("/proc") if p.isdigit()):
        if pid == mine or not owned_by(pid, uid):
            continue
        try:
            os.kill(int(pid), signal.SIGKILL)
            killed += 1
        except OSError:
            pass
    print("[reap] killed %d process(es) owned by uid %d" % (killed, uid))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
