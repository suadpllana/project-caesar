"""Kill anything still running as a given uid, then confirm nothing is left.

The run can double-fork, so a process it started may still be alive after the call
returns and could otherwise be writing while the verdict is being decided. pkill is not
in python:3.12-slim and no apt layer is reachable at build time, so this reads /proc
directly. It runs before grading, never after.
"""

import os
import signal
import sys
import time


def owners(uid):
    found = []
    me = os.getpid()
    try:
        entries = os.listdir("/proc")
    except OSError:
        return found
    for entry in entries:
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid == me:
            continue
        try:
            with open("/proc/%d/status" % pid) as fh:
                for line in fh:
                    if line.startswith("Uid:"):
                        if int(line.split()[1]) == uid:
                            found.append(pid)
                        break
        except (OSError, ValueError, IndexError):
            continue
    return found


def main(argv):
    if len(argv) < 2:
        return 0
    uid = int(argv[1])
    for attempt in range(3):
        live = owners(uid)
        if not live:
            break
        for pid in sorted(live):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        if attempt < 2:
            time.sleep(0.2)
    left = owners(uid)
    if left:
        sys.stderr.write("uid %d still has %d processes\n" % (uid, len(left)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
