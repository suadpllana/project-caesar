"""Kill anything still running as the sandbox uid after the trainer run returns.

Agent code can double-fork to outlive the call that started it, so the run's session is
reaped from the privileged side before the reward is derived. Written in Python rather
than pkill so the verifier image needs nothing beyond the base image.
"""

import os
import signal
import sys

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 1002


def main():
    killed = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid == os.getpid():
            continue
        try:
            if os.stat("/proc/%d" % pid).st_uid != TARGET:
                continue
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except OSError:
            continue
    print("reaped %d" % killed)


if __name__ == "__main__":
    main()
