"""Kill whatever the submitted feeder left running, identified by the uid it had to run under.

The first pass is started in a session of its own and under a wall clock. A process that
double forks walks out of both, so neither proves anything once the call has returned. The uid
does prove something: nothing else in this container runs as the sandbox user, so a live
process still holding it is a survivor of that pass, and a survivor is exactly the shape that
waits for grading to finish and then writes itself a reward. That door is already bolted - the
reward channel is root-owned and was locked before any agent code ran - and this closes the
other one, so nothing of the submission is still running while the grader reads its output.
"""
import os
import pathlib
import signal

SANDBOX = 1002
PROC = pathlib.Path("/proc")


def uid_of(entry):
    """The real uid a live process is running as, or None if it has already gone."""
    try:
        for row in (entry / "status").read_text(encoding="utf-8", errors="replace").splitlines():
            if row.startswith("Uid:"):
                field = row.split()
                if len(field) > 1 and field[1].isdigit():
                    return int(field[1])
                return None
    except OSError:
        return None
    return None


def survivors():
    mine = os.getpid()
    found = []
    for entry in PROC.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid != mine and uid_of(entry) == SANDBOX:
            found.append(pid)
    return found


def main():
    killed = []
    for pid in survivors():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        killed.append(pid)
    print("reaped %d: %s" % (len(killed), killed))


if __name__ == "__main__":
    main()
