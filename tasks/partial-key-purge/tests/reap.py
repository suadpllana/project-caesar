"""After the worker returns, nothing that ran as the sandbox uid may still be alive.

The timeout and the session wrap only the worker's own process tree; a submitted module that
double-forks leaves a child outside both, free to wait for the grade and then touch what the
grader wrote. The sandbox uid runs nothing but the worker and what it starts, so every process
still holding that uid is such a child. They are killed here, twice over in case one was forking
while the first pass ran, before pytest reads a byte. The reward directory is root-only as well;
this is the other half of the same guarantee.
"""
import os
import signal

SANDBOX = 1002


def owner(pid):
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("Uid:"):
                    real = line.split()[1:2]
                    return int(real[0]) if real and real[0].isdigit() else None
    except OSError:
        return None
    return None


def sweep():
    me = os.getpid()
    hit = 0
    for name in os.listdir("/proc"):
        if name.isdigit() and int(name) != me and owner(int(name)) == SANDBOX:
            try:
                os.kill(int(name), signal.SIGKILL)
                hit += 1
            except OSError:
                pass
    return hit


if __name__ == "__main__":
    print("reaped %d" % (sweep() + sweep()))
