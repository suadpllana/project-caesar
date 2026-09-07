import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import readings


def policy_dir(files):
    d = tempfile.mkdtemp(prefix="freq-")
    for fn in os.listdir(readings.REFERENCE):
        if fn.endswith(".py"):
            shutil.copyfile(os.path.join(readings.REFERENCE, fn),
                            os.path.join(d, fn))
    for name, src in files.items():
        with open(os.path.join(d, name), "w") as fh:
            fh.write(src)
    return d


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 400
    pop = readings.generated(n)
    want = {nm: readings.run(readings.REFERENCE, t) for nm, t in pop}
    print("%-22s %7s" % ("reading", "moves"))
    for name in sorted(readings.READINGS):
        d = policy_dir(readings.READINGS[name])
        bad = 0
        for nm, t in pop:
            try:
                got = readings.run(d, t)
            except Exception:
                got = ("raised",)
            if got != want[nm]:
                bad += 1
        print("%-22s %6.1f%%" % (name, 100.0 * bad / len(pop)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
