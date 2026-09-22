"""Nothing the submission started may still be running when the grader starts reading.

The worker runs in its own session under `timeout`, but a process that forks twice and calls
setsid again has left that session, and the clock never hears of it. What it cannot leave is its
real uid: the worker ran as 1002 and nothing else in this image does, so every process whose real
uid is 1002 belongs to the submission. Each round lists them from /proc/<pid>/status and kills
them, until a round finds none. The reward directory is root-only before the worker starts, so
this is not what protects the reward; it stops a survivor from rewriting the worker's output or
racing the grader while it runs.
"""
import os
import signal
import time

UID = 1002
ROUNDS = 5


def running_as_sandbox():
    found = []
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == os.getpid():
            continue
        try:
            with open("/proc/%s/status" % name, encoding="ascii", errors="replace") as fh:
                for row in fh:
                    if row.startswith("Uid:"):
                        if int(row.split()[1]) == UID:
                            found.append(int(name))
                        break
        except (OSError, ValueError, IndexError):
            continue
    return found


def main():
    total = 0
    for _ in range(ROUNDS):
        pids = running_as_sandbox()
        if not pids:
            break
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
                total += 1
            except ProcessLookupError:
                pass
        time.sleep(0.05)
    print("reaped %d process(es) running as uid %d" % (total, UID))


if __name__ == "__main__":
    main()
