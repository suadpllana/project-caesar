"""Run a program through the shipped tree and through the candidate reference."""
import subprocess
import sys

sys.path.insert(0, ".")
import fast

APP = "/home/user/project-caesar/tasks/anchor-mean-settle/environment/app_src"


def shipped(path):
    r = subprocess.run([sys.executable, "run_pan.py", path], cwd=APP,
                       capture_output=True, text=True)
    if r.returncode:
        return ["ERROR " + r.stderr.strip().splitlines()[-1]]
    return r.stdout.splitlines()


def main(path):
    lines = open(path).read().splitlines()
    a = shipped(path)
    b = fast.run(lines)
    print("%-26s %-26s" % ("shipped", "reference"))
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else ""
        y = b[i] if i < len(b) else ""
        print("%-26s %-26s %s" % (x, y, "" if x == y else "  <-- differs"))


if __name__ == "__main__":
    main(sys.argv[1])
