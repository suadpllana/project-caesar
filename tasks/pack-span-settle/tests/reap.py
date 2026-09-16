"""Kill whatever the replay stage left behind, choosing victims by uid.

The stage that runs submitted code is started in a session of its own and under a wall clock.
A double fork leaves both behind, so neither proves anything once the call has returned. What
the fork cannot leave behind is the uid it inherited, and nothing else in this container runs
as that uid, so any live process still holding it is a survivor of the replay stage. A
survivor is the exact shape that waits for grading to finish and then writes a reward.

The reward channel itself is root-owned and was locked before any submitted code ran, so this
is the second of two doors rather than the only one.
"""
import os
import signal

REPLAY_UID = 1002
STATUS = "/proc/%d/status"


def real_uid(pid):
    """The real uid of a live process, or None if it exited while we were reading it."""
    try:
        with open(STATUS % pid, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.startswith("Uid:"):
                    field = line.split()
                    if len(field) > 1 and field[1].isdigit():
                        return int(field[1])
                    return None
    except OSError:
        return None
    return None


def survivors():
    mine = os.getpid()
    for entry in os.listdir("/proc"):
        if entry.isdigit():
            pid = int(entry)
            if pid != mine and real_uid(pid) == REPLAY_UID:
                yield pid


def main():
    killed = 0
    for pid in survivors():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        killed += 1
    print("reaped %d" % killed)


if __name__ == "__main__":
    main()
