"""Kill whatever the submitted service left behind, by owner.

The worker runs in a session of its own and under a wall clock. A double fork leaves both
behind, so neither says anything about what is still running once the call has returned. The
uid does: nothing else in this container runs as the sandbox user, so a live process holding
it is a survivor, and a survivor is exactly the shape that waits for grading to finish and
then writes itself a reward. The reward channel is root-owned and was locked before any of
this started; this shuts the other door.

Two passes, because a process that is only sleeping should get the chance to exit on its own
before it is killed outright, and because the second pass is what proves the first worked.
"""
import os
import signal
import sys
import time


def owner(pid):
    """The real uid of a live process, or None if it went away while we looked."""
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    field = line.split()
                    return int(field[1]) if len(field) > 1 and field[1].isdigit() else None
    except OSError:
        return None
    return None


def survivors(uid, mine):
    for entry in os.listdir("/proc"):
        if entry.isdigit() and int(entry) != mine and owner(int(entry)) == uid:
            yield int(entry)


def sweep(uid, mine, sig):
    hit = 0
    for pid in survivors(uid, mine):
        try:
            os.kill(pid, sig)
        except OSError:
            continue
        hit += 1
    return hit


def main():
    uid = int(sys.argv[1]) if len(sys.argv) > 1 else 1002
    mine = os.getpid()
    asked = sweep(uid, mine, signal.SIGTERM)
    if asked:
        time.sleep(0.2)
    killed = sweep(uid, mine, signal.SIGKILL)
    left = sum(1 for _ in survivors(uid, mine))
    print("reap: asked %d, killed %d, left %d" % (asked, killed, left))
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main())
