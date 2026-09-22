"""Clear out anything the submission left running once stage one has returned.

Stage one runs in its own session under a wall clock, and a double fork walks out of both, so
when the call returns neither the session nor the clock says anything about what is still
alive. What does still hold is ownership: nothing else in this container runs as the pen user,
so the owner of /proc/<pid> is a complete test for "this came out of the submission".

This is the second lock and not the first. The reward lives in a root-owned directory made
0700 before any submitted line ran, so a survivor could not write it in any case; reaping shuts
the door on everything else a survivor could be doing while stage two reads.
"""
import os
import signal

PEN = 1002


def owned():
    mine = os.getpid()
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == mine:
            continue
        try:
            if entry.stat().st_uid == PEN:
                yield pid
        except OSError:
            continue


def main():
    gone = 0
    for pid in owned():
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue
        gone += 1
    print("left over from stage one, killed: %d" % gone)


if __name__ == "__main__":
    main()
