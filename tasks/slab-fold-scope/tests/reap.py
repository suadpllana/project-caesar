"""Whatever the submitted service left behind, by owner.

The worker is started in a session of its own and under a wall clock, and a double fork walks
out of both, so neither proves anything once the call has returned. The uid does: nothing else
in this container runs as the sandbox user, so a process still holding it is a survivor, and a
survivor is exactly the shape that waits for grading to end and then writes a reward. The reward
channel is root-owned and was locked before any of this ran; this shuts the other door.
"""
import os
import signal
import time

SANDBOX = 1002


def owner(pid):
    """The real uid of a non-zombie process, or None after it exits."""
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8", errors="replace") as fh:
            uid = None
            for line in fh:
                if line.startswith("State:") and line.split()[1] in ("Z", "X"):
                    return None
                if line.startswith("Uid:"):
                    uid = int(line.split()[1])
            return uid
    except (FileNotFoundError, ProcessLookupError):
        return None
    return None


def main():
    gone = 0
    deadline = time.monotonic() + 5
    while True:
        alive = [int(entry) for entry in os.listdir("/proc")
                 if entry.isdigit() and owner(int(entry)) == SANDBOX]
        if not alive:
            print("reaped %d; no live sandbox processes remain" % gone)
            return
        if time.monotonic() >= deadline:
            raise RuntimeError("sandbox processes survived cleanup")
        for pid in alive:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                continue
            gone += 1
        time.sleep(0.01)


if __name__ == "__main__":
    main()
