"""Kill whatever the unprivileged uid left behind.

pkill is not in this image, so the process table is read straight out of /proc. Anything
still owned by the run's uid after the run returned is a survivor - a double fork, a
background thread that outlived its parent - and it is killed before grading starts, so a
late write lands on an already locked, root owned reward file.
"""
import os
import signal
import sys


def owner(pid):
    try:
        with open("/proc/%d/status" % pid, "r", encoding="ascii", errors="ignore") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def main(argv):
    uid = int(argv[0]) if argv else 1003
    mine = os.getpid()
    killed = 0
    for name in sorted(os.listdir("/proc")):
        if not name.isdigit():
            continue
        pid = int(name)
        if pid == mine:
            continue
        if owner(pid) != uid:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except OSError:
            pass
    print("reaped %d" % killed)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
