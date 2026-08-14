"""Kill everything still running as a given uid.

pkill is not in python:3.12-slim and apt is not reachable at build time in every
environment, so this walks /proc instead. It runs after the sandboxed run returns and
before grading, so a process the agent double-forked cannot still be alive to write
anything while the verdict is being decided.
"""

import os
import signal
import sys


def uid_of(pid):
    try:
        with open("/proc/%s/status" % pid) as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def main(argv):
    if len(argv) < 2:
        return 0
    target = int(argv[1])
    me = os.getpid()
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        pid = int(name)
        if pid == me:
            continue
        if uid_of(name) == target:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
