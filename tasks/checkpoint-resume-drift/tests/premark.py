"""Survey the image for anything the trainer's uid owns or could write to.

test.sh runs this once before the run and test_outputs.py runs the same walk again
afterwards.  The graded question is the difference between the two: a path owned by the
trainer's uid that was not there before the run is a file the trainer created, which is a
way around the bounded checkpoint channel the whole task is built on and fails the
submission.

What is deliberately *not* graded is the survey's other half.  A directory the verifier
could not close - a volume the platform mounted, an inode the image did not create - is a
fact about the machine the verifier was handed, and an earlier version of this task failed
its own reference run by asserting that no such path existed.  It is recorded here so the
run is auditable, and it costs the submission nothing unless the trainer wrote to it.

The walk is bounded in both wall clock and node count so a large mounted volume cannot
stall the verifier.  If either bound is hit the survey says so, and the check that reads
it declines to grade rather than guessing.
"""

import json
import os
import stat
import sys
import time

UID = 1002

# The kernel's own filesystems keep nothing across a process, /dev belongs to the runtime,
# /logs is the harness's channel, and /work is the verifier's own, root-owned and
# rebuilt from the pristine tree every run.
SKIP = ("/proc", "/sys", "/dev", "/logs", "/work")

BUDGET = 60.0
NODES = 400000
MOST = 400


def _perm(st, bits):
    """Whether uid 1002, with no supplementary groups, holds one permission on a path."""
    if st.st_uid == UID:
        return bool(st.st_mode & (bits << 6))
    if st.st_gid == UID:
        return bool(st.st_mode & (bits << 3))
    return bool(st.st_mode & bits)


def _readonly_mounts():
    """Mount points nothing on this image can write to, whatever the modes say."""
    ro = set()
    try:
        with open("/proc/self/mounts") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 4 and "ro" in parts[3].split(","):
                    ro.add(parts[1])
    except OSError:
        pass
    return ro


def survey():
    """Every path the trainer's uid owns, and every path it could open for writing.

    Both lists are what the kernel would say, not what the modes look like in isolation:
    a path under a directory the uid cannot walk into is not reachable and does not count,
    and neither is anything on a read-only filesystem.
    """
    ro = _readonly_mounts()
    owned = []
    open_to = []
    seen = 0
    end = time.time() + BUDGET
    complete = True

    def keep(path, st):
        if st.st_uid == UID or st.st_gid == UID:
            if len(owned) < MOST:
                owned.append(path)
        if stat.S_ISDIR(st.st_mode):
            writable = _perm(st, 0o2) and _perm(st, 0o1)
        else:
            writable = _perm(st, 0o2)
        if writable and len(open_to) < MOST:
            open_to.append(path)

    for base, dirs, files in os.walk("/", onerror=lambda e: None):
        if time.time() > end or seen > NODES:
            complete = False
            break
        if base in ro:
            dirs[:] = []
            continue
        try:
            keep(base, os.lstat(base))
        except OSError:
            pass
        for name in dirs + files:
            seen += 1
            path = os.path.join(base, name)
            if path in SKIP:
                continue
            try:
                st = os.lstat(path)
            except OSError:
                continue
            if stat.S_ISLNK(st.st_mode):
                continue
            keep(path, st)
        dirs[:] = [d for d in dirs
                   if os.path.join(base, d) not in SKIP
                   and os.path.join(base, d) not in ro
                   and _walkable(os.path.join(base, d))]

    return {
        "complete": complete and len(owned) < MOST and len(open_to) < MOST,
        "owned": sorted(owned),
        "open": sorted(open_to),
        "at": time.time(),
    }


def _walkable(path):
    """Whether the walk carries on into a directory: the trainer's uid could have too."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return False
    return _perm(st, 0o1)


if __name__ == "__main__":
    with open(sys.argv[1], "w") as fh:
        json.dump(survey(), fh)
