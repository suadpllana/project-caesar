"""Take down anything the submitted store left running, and prove nothing survived.

The worker is started in a session of its own under a wall clock, but a double fork escapes
both, so neither the session id nor the timeout proves the run is over once the call has
returned. Ownership does: the sandbox uid runs nothing else, so a process still holding it
is a survivor, and a survivor is exactly the shape that waits for grading to finish and
then writes a reward. The reward channel is root-owned and locked long before this runs;
this closes the other half of the same hole.

Two passes. The first signals, the second reports what is still there, because a process
that ignores the first signal is worth seeing in the log rather than assuming away.
"""
import os
import signal
import time

SANDBOX = 1002


def owner(pid):
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8", errors="replace") as fh:
            for row in fh:
                if not row.startswith("Uid:"):
                    continue
                bits = row.split()
                return int(bits[1]) if len(bits) > 1 and bits[1].isdigit() else None
    except OSError:
        return None
    return None


def theirs():
    mine = os.getpid()
    out = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid != mine and owner(pid) == SANDBOX:
            out.append(pid)
    return out


def main():
    first = theirs()
    for pid in first:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    if first:
        time.sleep(0.5)
    left = theirs()
    print("reaped %d, still holding the sandbox uid: %d" % (len(first), len(left)))


if __name__ == "__main__":
    main()
