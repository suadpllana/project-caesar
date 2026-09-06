import os
import signal
import sys


def owners(uid):
    out = []
    for e in sorted(os.listdir("/proc")):
        if not e.isdigit():
            continue
        try:
            with open("/proc/%s/status" % e) as fh:
                body = fh.read()
        except OSError:
            continue
        for ln in body.splitlines():
            if ln.startswith("Uid:") and ln.split()[1] == str(uid):
                out.append(int(e))
                break
    return out


def main():
    uid = int(sys.argv[1])
    for pid in owners(uid):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


main()
