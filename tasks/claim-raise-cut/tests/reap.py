"""Take down anything the submitted service left behind.

The worker gets its own session and a wall clock, and a double fork walks out of both, so once
the call has returned the session id proves nothing. The uid does: the worker is the only thing
in this container running as the sandbox user, so a process still carrying that uid afterwards
is a survivor, and a survivor is the shape that waits for grading to finish and then writes a
reward. The reward channel is root-owned and was shut before any of this ran; this is the other
half of the same hole. A term first, then a kill for whatever ignored it.
"""
import os
import signal
import time

SANDBOX_UID = 1002


def owner(pid):
    try:
        return os.stat("/proc/%d" % pid).st_uid
    except OSError:
        return None


def survivors():
    mine = os.getpid()
    out = []
    with os.scandir("/proc") as entries:
        for entry in entries:
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            if pid != mine and owner(pid) == SANDBOX_UID:
                out.append(pid)
    return out


def send(pids, sig):
    left = []
    for pid in pids:
        try:
            os.kill(pid, sig)
            left.append(pid)
        except OSError:
            pass
    return left


def main():
    found = survivors()
    if found:
        send(found, signal.SIGTERM)
        time.sleep(0.2)
        send(survivors(), signal.SIGKILL)
    print("survivors %d" % len(found))


if __name__ == "__main__":
    main()
