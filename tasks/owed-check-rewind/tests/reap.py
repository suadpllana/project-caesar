"""Between the stages: stop every process the submitted code left running.

The worker runs under a wall clock in its own process group, but a process that forks twice and
starts a new session is in neither by the time the clock returns. It is still owned by the
unprivileged user, and nothing else in this container runs as that user, so ownership is the
test. A leftover cannot write the reward in any case - that directory is root's and was locked
before stage one began - but it could still be rewriting the scratch directory while stage two
reads it, so it goes before stage two starts.
"""
import os
import signal
import sys

RUNNER = int(os.environ.get("OCR_RUNNER", "2201"))


def owned_by_runner():
    me = os.getpid()
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == me:
            continue
        try:
            if os.stat("/proc/%s" % name).st_uid == RUNNER:
                yield int(name)
        except OSError:
            pass


def main():
    stopped = 0
    for _ in range(3):              # a leftover may fork again while the first pass runs
        found = list(owned_by_runner())
        if not found:
            break
        for pid in found:
            try:
                os.kill(pid, signal.SIGKILL)
                stopped += 1
            except OSError:
                pass
    print("leftover processes stopped: %d" % stopped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
