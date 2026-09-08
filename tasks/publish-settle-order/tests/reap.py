"""Kill whatever the submitted host left running.

The worker is started in its own session and under a wall-clock timeout, but a double fork
escapes both, so the session id proves nothing once the call has returned. Ownership does: the
worker is the only thing that runs as the sandbox uid, so any process still holding that uid
after it returns is a survivor, and a survivor is exactly the shape that waits for grading to
finish and then writes a reward. The reward channel is root-owned and already locked by the time
this runs; this closes the other half of the same hole.
"""
import os
import signal

SANDBOX_UID = 1002


def _uid_of(pid):
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("Uid:"):
                    bits = line.split()
                    return int(bits[1]) if len(bits) > 1 and bits[1].isdigit() else None
    except OSError:
        return None
    return None


def main():
    mine = os.getpid()
    killed = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid == mine or _uid_of(pid) != SANDBOX_UID:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except OSError:
            pass
    print("reaped %d" % killed)


if __name__ == "__main__":
    main()
