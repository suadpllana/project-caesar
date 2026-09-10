"""Nothing owned by the sandbox uid may outlive the worker.

The worker is started in its own session under a wall clock, and both of those are escaped by
a double fork: once the call returns, the session id proves nothing about what is still
running. Ownership does prove something. The sandbox uid runs exactly one thing in this
container, so any process still holding it after the worker returns is a survivor, and a
survivor that sleeps and then writes a reward is the whole reason the reward channel is
root-owned. This closes the other half: the channel cannot be written, and the writer does not
get to wait around either.

Two passes, because a process can fork between the listing and the kill. The second pass is
what the report is drawn from, so a survivor that outlives both is visible rather than assumed
away.
"""
import os
import signal

SANDBOX_UID = 1002


def owner(pid):
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.startswith("Uid:"):
                    continue
                field = line.split()
                return int(field[1]) if len(field) > 1 and field[1].isdigit() else None
    except OSError:
        return None
    return None


def survivors():
    mine = os.getpid()
    found = []
    for entry in os.listdir("/proc"):
        if entry.isdigit() and int(entry) != mine and owner(int(entry)) == SANDBOX_UID:
            found.append(int(entry))
    return found


def main():
    killed = []
    for _pass in (1, 2):
        for pid in survivors():
            try:
                os.kill(pid, signal.SIGKILL)
                killed.append(pid)
            except OSError:
                pass
    left = survivors()
    print("reaped %d, still holding uid %d: %s" % (len(killed), SANDBOX_UID, left or "none"))


if __name__ == "__main__":
    main()
