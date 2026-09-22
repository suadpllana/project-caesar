"""Reap the submission's leftovers: every live process still running as the sandbox uid.

`setsid` and `timeout` bound the worker's own session, not what it forked out of it, so a
process that double-forked is invisible to both and can sit waiting for the grader to finish.
What it cannot shed is its uid. Nothing else in the verifier container runs as 1002, so "has
1002 among its uids" is a complete description of what the submission left alive.

The sweep repeats until a pass finds nothing, because a survivor may fork while the pass
before is killing its parent; zombies are already dead and are left to whoever reaps them.
The verdict directory is root-only and 0700 before any submitted code runs, so this is the
second guard on the reward, not the first.
"""
import os
import signal

SANDBOX = 1002
PASSES = 20


def _status(pid):
    """The `State` and `Uid` lines of /proc/<pid>/status, or None once the process is gone."""
    fields = {}
    try:
        with open("/proc/%d/status" % pid, encoding="ascii", errors="replace") as fh:
            for line in fh:
                key, _sep, value = line.partition(":")
                if key in ("State", "Uid"):
                    fields[key] = value.split()
    except OSError:
        return None
    return fields


def live_sandbox_pids():
    me = os.getpid()
    found = []
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == me:
            continue
        fields = _status(int(name))
        if not fields or fields.get("State", ["?"])[0] == "Z":
            continue
        if str(SANDBOX) in fields.get("Uid", []):
            found.append(int(name))
    return found


def sweep():
    killed = set()
    for _ in range(PASSES):
        pids = live_sandbox_pids()
        if not pids:
            break
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                continue
            killed.add(pid)
    return len(killed)


if __name__ == "__main__":
    print("survivors killed: %d" % sweep())
