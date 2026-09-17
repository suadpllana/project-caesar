"""Kill anything still running as the sandbox user, and say whether any of it survived.

The worker gets its own session and a wall clock. Neither binds a process that double-forks out
of both, and such a process is exactly the shape that waits for grading to end and then writes a
reward. What does bind it is ownership: the sandbox uid runs nothing else in this container, so
every process still holding that uid after the worker returns is a survivor.

The reward channel is root-owned and was locked before any of this ran, so a survivor that gets
as far as opening it is denied. This shuts the other door, and it reports what it found so the
run is not silent about it.
"""
import os
import signal
import time

UID = 1002
GRACE = 0.4


def uid_of(pid):
    """The real uid of a process, or None if it is gone or unreadable."""
    try:
        with open("/proc/%d/status" % pid, "rb") as handle:
            for raw in handle:
                if raw.startswith(b"Uid:"):
                    bits = raw.split()
                    return int(bits[1]) if len(bits) > 1 else None
    except OSError:
        return None
    return None


def theirs():
    mine = os.getpid()
    found = []
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid != mine and uid_of(pid) == UID:
            found.append(pid)
    return found


def main():
    first = theirs()
    for pid in first:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    if first:
        time.sleep(GRACE)
    left = theirs()
    print("sandbox processes found %d, still alive %d" % (len(first), len(left)))
    if left:
        print("survivors: %s" % ", ".join(str(pid) for pid in left))


if __name__ == "__main__":
    main()
