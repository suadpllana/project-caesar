"""Kill whatever the submitted panel left running, identified by who owns it.

Stage one is started in a session of its own and under a wall clock. A process that double
forks walks out of both, so by the time the call returns neither says anything about what is
still alive. The uid does: this image gives uid 1002 to nothing but that stage, so any live
process still holding it is a survivor, and a survivor is exactly the shape that waits for
grading to finish and then writes a reward of its own. That door is already shut - the reward
channel is root-owned and was locked before stage one began - and this shuts the other one.
"""
import os
import signal

STAGE_ONE = 1002


def holder(pid):
    """The real uid behind a pid, or None if the process went away mid-read."""
    path = "/proc/%d/status" % pid
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    parts = line.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        return int(parts[1])
                    return None
    except OSError:
        return None
    return None


def survivors():
    mine = os.getpid()
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid != mine and holder(pid) == STAGE_ONE:
            yield pid


def main():
    killed = 0
    for pid in list(survivors()):
        try:
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except OSError:
            pass
    print("reaped %d" % killed)


if __name__ == "__main__":
    main()
