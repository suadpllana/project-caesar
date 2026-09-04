"""Kill anything the unprivileged run left behind.

pkill is not in the image and apt cannot be reached from the build, so the
process table is read out of /proc directly.
"""

import os
import signal
import sys


def owned_by(uid):
    out = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open("/proc/%s/status" % entry) as fh:
                for row in fh:
                    if row.startswith("Uid:"):
                        if int(row.split()[1]) == uid:
                            out.append(int(entry))
                        break
        except (IOError, OSError):
            continue
    return out


def main():
    uid = int(sys.argv[1])
    mine = os.getpid()
    for pid in owned_by(uid):
        if pid == mine:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


if __name__ == "__main__":
    main()
