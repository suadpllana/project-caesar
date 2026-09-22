"""Once the reader's call returns, nothing the submission started may still be running.

`timeout` and `setsid --wait` only bound the reader's own session. A process that forked twice
and started a session of its own is outside both, so it outlives the call - which is exactly how
something would wait for grading to finish and then touch the result. It could not write the
reward anyway, since /logs/verifier is root's and 0700 before the reader starts; this makes sure
it is not running at all while the grader reads. Nothing else in the container runs as the
reader's uid, so every process that holds it came from the submission.
"""
import os
import signal

READER_UID = 1002


def holders():
    """Pids of live processes whose real, effective, saved or filesystem uid is the reader's."""
    out = []
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == os.getpid():
            continue
        uids, state = (), ""
        try:
            with open("/proc/%s/status" % name, encoding="ascii", errors="replace") as fh:
                for line in fh:
                    if line.startswith("State:"):
                        state = line.split()[1]
                    elif line.startswith("Uid:"):
                        uids = [int(x) for x in line.split()[1:]]
        except (OSError, ValueError):
            continue
        if state != "Z" and READER_UID in uids:
            out.append(int(name))
    return out


def main():
    killed = set()
    # A process can fork between the listing and the kill, so sweep until a pass finds nothing.
    for _ in range(5):
        pids = [p for p in holders() if p not in killed]
        if not pids:
            break
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                continue
            killed.add(pid)
    print("survivors killed: %d" % len(killed))


if __name__ == "__main__":
    main()
