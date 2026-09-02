"""Kill anything the run left behind.

A submission that double-forks outlives the wall clock its parent was given, so the
processes belonging to the run's uid are walked out of /proc and signalled here. pkill is
not in the base image and apt is out of reach, so this reads the filesystem directly.
"""
import os
import sys


def owner(pid):
    try:
        with open("/proc/%s/status" % pid) as h:
            for ln in h:
                if ln.startswith("Uid:"):
                    return int(ln.split()[1])
    except OSError:
        return None
    return None


def main(uid):
    mine = os.getpid()
    hit = 0
    for e in sorted(os.listdir("/proc")):
        if not e.isdigit() or int(e) == mine:
            continue
        if owner(e) != uid:
            continue
        try:
            os.kill(int(e), 9)
            hit += 1
        except OSError:
            pass
    print("[reap] signalled %d" % hit)


if __name__ == "__main__":
    main(int(sys.argv[1]))
