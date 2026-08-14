"""Kill anything still running as a given uid, then confirm nothing is left.

The scheduler run happens in its own session so a process it double forked can be found
afterwards. pkill is not in the base image and apt is not reachable at build time, so this
reads /proc directly. It runs between the run and the grading, which is the window in which a
survivor would otherwise still be able to write something.
"""

import os
import signal
import sys


def owners(pid):
    try:
        with open("/proc/%s/status" % pid) as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def alive(uid):
    out = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == os.getpid():
            continue
        if owners(pid) == uid:
            out.append(int(pid))
    return out


def main(argv):
    uid = int(argv[1]) if len(argv) > 1 else 1002
    for sig in (signal.SIGKILL, signal.SIGKILL):
        for pid in alive(uid):
            try:
                os.kill(pid, sig)
            except OSError:
                pass
    left = alive(uid)
    if left:
        sys.stderr.write("processes survived as uid %d: %r\n" % (uid, left))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
