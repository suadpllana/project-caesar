"""Leave nothing of the run behind.

The run gets its own session and a wall clock, but a double fork walks out of
both, so the clock proves nothing by itself. There is no pkill in the slim image
and the verifier may not reach the network at trial time, so /proc is read
directly: anything still owned by the unprivileged uid is signalled, politely
first and then not.

Exit status is always 0. A survivor that will not die is reported on stderr and
graded on by the attestations, which is stricter than refusing to grade at all.
"""

import errno
import os
import signal
import sys
import time

ROUNDS = ((signal.SIGTERM, 0.4), (signal.SIGTERM, 0.2), (signal.SIGKILL, 0.2))


def uid_of(entry):
    try:
        handle = open("/proc/%s/status" % entry)
    except (IOError, OSError):
        return None
    try:
        for line in handle:
            if line[:4] == "Uid:":
                return int(line.split()[1])
    except (ValueError, IndexError, IOError):
        return None
    finally:
        handle.close()
    return None


def owned_by(uid):
    mine = os.getpid()
    found = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit() or int(entry) == mine:
            continue
        if uid_of(entry) == uid:
            found.append(int(entry))
    return found


def clear(uid):
    for sig, wait in ROUNDS:
        alive = owned_by(uid)
        if not alive:
            return []
        for pid in alive:
            try:
                os.kill(pid, sig)
            except OSError as exc:
                if exc.errno not in (errno.ESRCH, errno.EPERM):
                    raise
        time.sleep(wait)
    return owned_by(uid)


def main(argv):
    left = clear(int(argv[1]))
    if left:
        sys.stderr.write("survivors: %s\n" % " ".join(str(p) for p in left))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
