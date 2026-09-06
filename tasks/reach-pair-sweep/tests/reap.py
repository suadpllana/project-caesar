"""Kill anything the submitted collector left behind.

The worker runs in its own session, but a double fork escapes a process group, so the only
reliable sweep is by owner: every process still running as the sandbox uid once the worker has
returned is a survivor, and a survivor is exactly what would try to write a reward after the
grading is done. The reward channel is already root-owned and locked by then; this closes the
other half.
"""
import os
import pathlib
import signal

SANDBOX = 1002


def survivors():
    me = os.getpid()
    for entry in sorted(pathlib.Path("/proc").iterdir()):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == me:
            continue
        try:
            status = (entry / "status").read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in status.splitlines():
            if line.startswith("Uid:"):
                parts = line.split()
                if len(parts) > 1 and parts[1].isdigit() and int(parts[1]) == SANDBOX:
                    yield pid
                break


def main():
    found = sorted(survivors())
    for pid in found:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    print("reaped %d survivor(s)" % len(found))


if __name__ == "__main__":
    main()
