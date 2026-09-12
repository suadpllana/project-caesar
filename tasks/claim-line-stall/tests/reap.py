"""Kill whatever the submitted service left running, identified by the uid it ran under.

The worker is given its own session and a wall clock, and a process that double forks walks
out of both, so neither proves anything once the call has returned. Ownership does: the
sandbox uid is used by nothing else in this container, so any live process still holding it
is a survivor of the run. A survivor is exactly the shape that waits for grading to finish
and then writes a reward, which is why this runs before the grading stage rather than after
it. The reward channel itself is root-owned and was locked before any of this started; this
closes the other door.
"""
import os
import signal

SANDBOX = 1002


def held_by(pid):
    """The real uid of a live process, or None if it went away while we looked."""
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    parts = line.split()
                    return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    except OSError:
        return None
    return None


def main():
    self = os.getpid()
    killed = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid == self or held_by(pid) != SANDBOX:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        killed += 1
    print("reaped %d" % killed)


if __name__ == "__main__":
    main()
