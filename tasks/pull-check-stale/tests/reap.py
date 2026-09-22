"""Clear out anything the submitted engine left running.

Half one is launched into its own session with a wall clock on it, and neither of those
survives a double fork: once the call returns, a process that walked out of both is still
there, and the shape that matters is the one that waits for grading to end and then writes a
reward. So the reward channel is a root-owned 0700 directory locked before any submitted line
ran - that is the lock that actually holds - and this is the second one, which shuts the door
on whatever else a survivor could still be doing while the grader reads.

Ownership is the test. Nothing else in this container runs as the sandbox uid, so a process
owned by it came from half one. The uid is read out of /proc/<pid>/status rather than off the
directory, because a process that changed its own name or cwd has not changed that line.
"""
import os
import signal

SANDBOX = 1002


def owner(pid):
    """The real uid on the Uid: line of /proc/<pid>/status, or None if it has gone."""
    try:
        with open("/proc/%d/status" % pid, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def theirs():
    mine = os.getpid()
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid != mine and owner(pid) == SANDBOX:
            yield pid


def main():
    # Two passes: the first can orphan children that the second then finds.
    gone = 0
    for _attempt in (1, 2):
        for pid in list(theirs()):
            try:
                os.kill(pid, signal.SIGKILL)
                gone += 1
            except OSError:
                continue
    print("sandbox processes cleared: %d" % gone)


if __name__ == "__main__":
    main()
