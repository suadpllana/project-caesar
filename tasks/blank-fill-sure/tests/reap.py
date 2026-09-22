"""After the worker returns, end every process the sandbox user still owns.

The worker ran in its own session under a wall clock, but a process that double-forks leaves
both behind, so neither says anything about what is still alive. What does hold is ownership:
nothing else in this container runs as the sandbox uid, so a live process owned by it came from
the submission. Such a process could be waiting for grading to end in order to write something,
or still touching the worker's output while the grader reads it.

The reward directory was locked to root before any submitted code ran, so this is the second
lock and not the first: it keeps a survivor from interfering with grading at all.
"""
import os
import signal

SANDBOX = 1002


def owned_by_sandbox():
    me = os.getpid()
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == me:
            continue
        try:
            if os.stat("/proc/%s" % name).st_uid == SANDBOX:
                yield int(name)
        except OSError:
            continue


def main():
    ended = 0
    for pid in list(owned_by_sandbox()):
        try:
            os.kill(pid, signal.SIGKILL)
            ended += 1
        except OSError:
            pass
    print("sandbox processes ended: %d" % ended)


if __name__ == "__main__":
    main()
