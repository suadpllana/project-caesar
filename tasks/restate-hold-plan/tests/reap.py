"""After stage one returns, stop everything the submission may have left running.

Stage one runs in a session of its own under a clock, and neither says anything about a process
that double-forked out of both. Such a survivor is the shape that waits for grading to finish and
then tries to write a reward. It cannot: the reward directory was locked to root before stage one
started. This closes the rest - nothing of the submission is still running while stage two reads
its record. Nothing else in the verifier runs as uid 1002, so the uid alone identifies it.

A survivor can fork while it is being killed, so the sweep repeats until a pass finds nobody.
"""
import os
import signal

PLANNER_UID = 1002


def owned_by_planner():
    found = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit() or int(entry) == os.getpid():
            continue
        try:
            with open("/proc/%s/status" % entry, encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("Uid:"):
                        if int(line.split()[1]) == PLANNER_UID:
                            found.append(int(entry))
                        break
        except (OSError, ValueError):
            continue
    return found


def main():
    total = 0
    for _sweep in range(50):
        pids = owned_by_planner()
        if not pids:
            break
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
                total += 1
            except OSError:
                pass
    print("processes left by stage one and killed: %d" % total)


if __name__ == "__main__":
    main()
