"""What the execution limit actually separates.

The reference indexes the log once; the readings below stay exactly correct and look it up
by walking the log for every command, or settle every race by scanning the log's answers.
Both are what a first implementation writes. This times all of them on the two scale
families so the limit in the brief is a measurement rather than a guess.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "replay-match-drift"
PARTS = ("tab", "edge", "pair", "pend", "sigq", "ver")

SCAN_TAB = '''
class Tab(object):
    def __init__(self, log):
        self.log = log

    def slot(self, kind, i):
        seen = 0
        for pos, (ev, args) in enumerate(self.log):
            if ev == "go" and args[0] == kind:
                if seen == i:
                    return pos, args[1]
                seen += 1
        return None

    def answer(self, kind, name, j):
        seen = 0
        for pos, (ev, args) in enumerate(self.log):
            if ev == "ok" and args[0] == kind and args[1] == name:
                if seen == j:
                    return pos, int(args[2])
                seen += 1
        return None

    def signal(self, tag, j):
        seen = 0
        for pos, (ev, args) in enumerate(self.log):
            if ev == "sig" and args[0] == tag:
                if seen == j:
                    return pos, int(args[1])
                seen += 1
        return None

    def choice(self, key, j):
        seen = 0
        for pos, (ev, args) in enumerate(self.log):
            if ev == "ch" and args[0] == key:
                if seen == j:
                    return pos, int(args[1])
                seen += 1
        return None

    def issued(self):
        out = []
        seen = {}
        for pos, (ev, args) in enumerate(self.log):
            if ev == "go":
                at = seen.get(args[0], 0)
                seen[args[0]] = at + 1
                out.append((pos, args[0], at))
        return out
'''

HALF_TAB = """
class Tab(object):
    def __init__(self, log):
        self.log = log
        self.go = {}
        self.order = []
        seen = {}
        for pos, (ev, args) in enumerate(log):
            if ev == "go":
                at = seen.get(args[0], 0)
                seen[args[0]] = at + 1
                self.go.setdefault(args[0], []).append((pos, args[1]))
                self.order.append((pos, args[0], at))

    def slot(self, kind, i):
        row = self.go.get(kind)
        if row is None or i >= len(row):
            return None
        return row[i]

    def answer(self, kind, name, j):
        seen = 0
        for pos, (ev, args) in enumerate(self.log):
            if ev == "ok" and args[0] == kind and args[1] == name:
                if seen == j:
                    return pos, int(args[2])
                seen += 1
        return None

    def signal(self, tag, j):
        seen = 0
        for pos, (ev, args) in enumerate(self.log):
            if ev == "sig" and args[0] == tag:
                if seen == j:
                    return pos, int(args[1])
                seen += 1
        return None

    def choice(self, key, j):
        seen = 0
        for pos, (ev, args) in enumerate(self.log):
            if ev == "ch" and args[0] == key:
                if seen == j:
                    return pos, int(args[1])
                seen += 1
        return None

    def issued(self):
        return self.order
"""


def stage(which):
    room = pathlib.Path(tempfile.mkdtemp())
    shutil.copytree(TASK / "environment" / "app_src", room / "app")
    for part in PARTS:
        shutil.copy(TASK / "solution" / (part + ".py"), room / "app" / "dur" / (part + ".py"))
    if which == "scan-log":
        (room / "app" / "dur" / "tab.py").write_text(SCAN_TAB, encoding="utf-8", newline="\n")
    if which == "scan-answers":
        (room / "app" / "dur" / "tab.py").write_text(HALF_TAB, encoding="utf-8", newline="\n")
    return room


def main():
    sys.path.insert(0, str(TASK / "tests"))
    import gen
    work = [(fam, name, lines) for fam, name, lines in gen.programs("time", 1)
            if fam in ("long", "wide")]
    print("%d scale programs, %d lines each on average"
          % (len(work), sum(len(l) for _f, _n, l in work) // len(work)), flush=True)
    for which in ("reference", "scan-log", "scan-answers"):
        room = stage(which)
        spent = {}
        for fam, name, lines in work:
            body = "\n".join(lines) + "\n"
            (room / "prog.txt").write_text(body, encoding="utf-8", newline="\n")
            start = time.time()
            done = subprocess.run(
                [sys.executable, "-c",
                 "import sys;sys.path.insert(0,'.');import run_dur;"
                 "run_dur.run(open(sys.argv[1]).read())", str(room / "prog.txt")],
                cwd=room / "app", capture_output=True, text=True, timeout=1200)
            took = time.time() - start
            spent[fam] = spent.get(fam, 0.0) + took
            if done.returncode:
                print("  %s %s FAILED %s" % (which, name, done.stderr.strip()[-200:]))
        print("%-10s  %s  total %.1fs"
              % (which, "  ".join("%s %.1fs" % (k, v) for k, v in sorted(spent.items())),
                 sum(spent.values())), flush=True)
        shutil.rmtree(room)


if __name__ == "__main__":
    main()
