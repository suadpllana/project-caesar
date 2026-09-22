"""Kill whatever still runs as the sandbox user once the worker has returned.

The worker runs in its own session under a wall clock, but a double fork escapes both, and a
process that outlives the call is the exact shape of an attack that waits for grading to end
and then writes a reward. What a survivor cannot escape is its uid: nothing else in this
container runs as the sandbox user, so ownership alone says what came from the submission.

The reward directory was made root-only before any submitted line ran, so a survivor could
not write it in any case. This closes everything else a survivor might still be doing while
the grader reads.
"""
import os
import signal

SANDBOX_UID = 1002


def owned_by_sandbox():
    me = os.getpid()
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit() or int(entry.name) == me:
            continue
        try:
            if entry.stat().st_uid == SANDBOX_UID:
                yield int(entry.name)
        except OSError:
            continue


def main():
    count = 0
    for pid in list(owned_by_sandbox()):
        try:
            os.kill(pid, signal.SIGKILL)
            count += 1
        except OSError:
            pass
    print("reaped %d process(es) of uid %d" % (count, SANDBOX_UID))


if __name__ == "__main__":
    main()
