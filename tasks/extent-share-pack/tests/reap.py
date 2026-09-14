"""Kill anything the submitted half left running, chosen by the uid it runs as.

The unprivileged half is started in its own session under a clock, and a process that double
forks walks out of both, so neither is evidence once the call returns. The uid is: only that half
ever runs as 1002 in this container, so any process still holding it outlived its parent on
purpose, and the shape that does so is one waiting for grading to end before writing a reward.
The reward file is root-owned inside a directory locked before any of this started; this closes
the second way in rather than the first.
"""
import os
import pathlib
import signal

LOW = 1002


def uid_of(proc):
    """The real uid recorded for a live process, or None if it has already gone."""
    try:
        for row in (proc / "status").read_text(encoding="utf-8", errors="replace").splitlines():
            if row.startswith("Uid:"):
                bits = row.split()
                return int(bits[1]) if len(bits) > 1 and bits[1].isdigit() else None
    except OSError:
        return None
    return None


def survivors():
    me = os.getpid()
    for proc in pathlib.Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        pid = int(proc.name)
        if pid != me and uid_of(proc) == LOW:
            yield pid


def main():
    killed = 0
    for pid in list(survivors()):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        killed += 1
    print("killed %d leftover process(es)" % killed)


if __name__ == "__main__":
    main()
