"""Whatever the submitted service left behind, by owner.

The worker is started in a session of its own and under a wall clock, and a double fork walks
out of both, so neither proves anything once the call has returned. The uid does: nothing else
in this container runs as the sandbox user, so a process still holding it is a survivor, and a
survivor is exactly the shape that waits for grading to end and then writes a reward. The reward
channel is root-owned and was locked before any of this ran; this shuts the other door.
"""
import os
import signal

SANDBOX = 1002


def owner(pid):
    """The real uid of a live process, or None if it went away while we looked."""
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.startswith("Uid:"):
                    continue
                field = line.split()
                return int(field[1]) if len(field) > 1 and field[1].isdigit() else None
    except OSError:
        return None
    return None


def main():
    self = os.getpid()
    gone = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid == self or owner(pid) != SANDBOX:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        gone += 1
    print("reaped %d" % gone)


if __name__ == "__main__":
    main()
