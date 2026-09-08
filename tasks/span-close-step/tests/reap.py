"""Clear out anything the submitted trainer left running, before grading starts.

The worker is launched in its own session, so the ordinary sweep is by session id:
one signal to the group takes down the children that stayed inside it. What that
misses is the case worth defending against - code that double-forks, calls
`setsid` itself and so leaves the group entirely - and the only handle left on
such a process is the uid it runs under. So this sweeps twice: by session first,
because that is precise, then by owner, because that is complete. It ends by
counting what is still alive as the sandbox user and saying so, since a nonzero
count after both passes is a fact the handover needs rather than something to
swallow quietly.

The reward channel is root-owned and locked before any of this runs, so a survivor
that outlives both passes still cannot write a verdict. This closes the other half:
a survivor cannot sit in the background and rewrite the worker's output while the
grader is reading it.
"""
import os
import pathlib
import signal
import time

SANDBOX = 1002
PROC = pathlib.Path("/proc")


def owner(pid):
    try:
        text = (PROC / str(pid) / "status").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("Uid:"):
            bits = line.split()
            if len(bits) > 1 and bits[1].isdigit():
                return int(bits[1])
            return None
    return None


def session(pid):
    try:
        return os.getsid(pid)
    except OSError:
        return None


def live():
    mine = os.getpid()
    for entry in PROC.iterdir():
        if entry.name.isdigit():
            pid = int(entry.name)
            if pid != mine and owner(pid) == SANDBOX:
                yield pid


def sweep(sig):
    hit = 0
    groups = set()
    for pid in sorted(live()):
        sid = session(pid)
        if sid and sid != os.getsid(os.getpid()):
            groups.add(sid)
    for sid in sorted(groups):
        try:
            os.killpg(sid, sig)
            hit += 1
        except OSError:
            pass
    for pid in sorted(live()):
        try:
            os.kill(pid, sig)
            hit += 1
        except OSError:
            pass
    return hit


def main():
    first = sweep(signal.SIGTERM)
    time.sleep(0.2)
    second = sweep(signal.SIGKILL)
    time.sleep(0.2)
    left = len(list(live()))
    print("reap: signalled %d, then %d; %d still alive" % (first, second, left))


if __name__ == "__main__":
    main()
