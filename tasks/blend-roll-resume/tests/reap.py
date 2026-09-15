"""Kill anything still running as the sandbox uid once the submitted feed has returned.

The stage that runs agent code is started in its own session and under a wall clock. A process
that double-forks leaves the session and outlives the clock, so neither is evidence that it is
gone. Ownership is: nothing else in this image runs as uid 1002, so a live process holding that
uid after the call is a survivor, and a survivor is the shape that waits for grading to finish
and then writes a reward.

The reward channel is root-owned inside a directory locked to mode 700 before any of this ran,
so a survivor could not write it anyway. This closes the other half: it also stops a survivor
holding the work directory open or racing the grader for it.

Ownership is read by stat on /proc/<pid> rather than by parsing the status file, so a pid that
disappears mid-sweep raises rather than returning a half-parsed uid.
"""
import os
import signal

SANDBOX_UID = 1002


def candidates():
    """Live pids owned by the sandbox uid, this process excluded."""
    mine = os.getpid()
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == mine:
            continue
        try:
            if entry.stat(follow_symlinks=False).st_uid == SANDBOX_UID:
                yield pid
        except OSError:
            continue


def sweep(sig):
    killed = 0
    for pid in candidates():
        try:
            os.kill(pid, sig)
        except OSError:
            continue
        killed += 1
    return killed


def main():
    asked = sweep(signal.SIGTERM)
    forced = sweep(signal.SIGKILL)
    left = sum(1 for _ in candidates())
    print("reap: signalled %d, forced %d, still up %d" % (asked, forced, left))


if __name__ == "__main__":
    main()
