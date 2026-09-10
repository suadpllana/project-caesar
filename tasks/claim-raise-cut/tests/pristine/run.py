import sys

from hold import out, txn


def read(path):
    steps = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            f = line.split()
            if f[0] == "take" and len(f) == 4:
                steps.append((f[0], f[1], f[2], f[3]))
            elif f[0] == "drop" and len(f) == 3:
                steps.append((f[0], f[1], f[2]))
            elif f[0] == "end" and len(f) == 2:
                steps.append((f[0], f[1]))
            else:
                raise SystemExit("bad step: %s" % line)
    return steps


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: run.py <program>")
    tr = out.Trace()
    svc = txn.Svc(tr)
    for st in read(argv[1]):
        svc.step(st)
    sys.stdout.write(tr.text() + "\n")


if __name__ == "__main__":
    main(sys.argv)
