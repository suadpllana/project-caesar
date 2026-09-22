"""What the execution limit actually separates.

Two readings settle every rule the way the reference does and lose on cost alone. One looks
every command and answer up by walking the recorded history instead of indexing it once. The
other - the one the limit is really for - keeps the waiting branches in a list and walks it
at every step for the one whose mark is smallest, which is what a first implementation
writes and what no amount of ordinary dict indexing repairs.

    python3 -u authoring/replay-match-drift/timing.py
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "replay-match-drift"
PARTS = ("tab.py", "edge.py", "pair.py", "hold.py", "sched.py", "wake.py", "ver.py")

SCAN_SCHED = '''
class Branch(object):
    __slots__ = ("bid", "pc", "acc", "due", "state")

    def __init__(self, bid, pc):
        self.bid = bid
        self.pc = pc
        self.acc = 0
        self.due = None
        self.state = "ready"


class Sched(object):
    def __init__(self):
        self.all = []
        self.mark = {}

    def open(self, pc):
        made = Branch(len(self.all), pc)
        self.all.append(made)
        return made.bid

    def pick(self):
        best = None
        for who in self.all:
            if who.state == "ready":
                if best is None or who.bid < best.bid:
                    best = who
        if best is not None:
            best.state = "running"
            return best
        for who in self.all:
            if who.state != "parked":
                continue
            mark = self.mark.get(who.bid)
            if mark is None:
                continue
            if best is None or mark < self.mark[best.bid]:
                best = who
        if best is None:
            return None
        best.state = "running"
        return best

    def park(self, who, mark):
        who.state = "parked"
        self.mark[who.bid] = mark

    def close(self, who):
        who.state = "ended"

    def release(self):
        for who in self.all:
            if who.state == "parked":
                who.state = "ready"
                self.mark[who.bid] = None
'''

SCAN_TAB = '''
class Tab(object):
    def __init__(self, log):
        self.log = log

    def _nth(self, want, keys, i):
        seen = 0
        for pos, (ev, args) in enumerate(self.log):
            if ev == want and all(args[at] == key for at, key in keys):
                if seen == i:
                    return pos, args
                seen += 1
        return None

    def slot(self, kind, i):
        got = self._nth("go", ((0, kind),), i)
        return None if got is None else (got[0], got[1][1])

    def answer(self, kind, name, j):
        got = self._nth("ok", ((0, kind), (1, name)), j)
        return None if got is None else (got[0], int(got[1][2]))

    def signal(self, tag, j):
        got = self._nth("sig", ((0, tag),), j)
        return None if got is None else (got[0], int(got[1][1]))

    def choice(self, key, j):
        got = self._nth("ch", ((0, key),), j)
        return None if got is None else (got[0], int(got[1][1]))

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


def stage(which):
    room = pathlib.Path(tempfile.mkdtemp())
    shutil.copytree(TASK / "environment" / "app_src", room / "app",
                    ignore=shutil.ignore_patterns("__pycache__"))
    for part in PARTS:
        shutil.copy(TASK / "solution" / part, room / "app" / "dur" / part)
    if which == "scan-sched":
        (room / "app" / "dur" / "sched.py").write_text(SCAN_SCHED, encoding="utf-8",
                                                       newline="\n")
    if which == "scan-log":
        (room / "app" / "dur" / "tab.py").write_text(SCAN_TAB, encoding="utf-8",
                                                     newline="\n")
    return room


def main():
    sys.path.insert(0, str(TASK / "tests"))
    import gen
    work = [(fam, name, lines) for fam, name, lines in gen.programs("time", 1)
            if fam in ("long", "wide")]
    print("%d scale programs, %d lines each on average"
          % (len(work), sum(len(rows) for _f, _n, rows in work) // len(work)), flush=True)
    for which in ("reference", "scan-sched", "scan-log"):
        room = stage(which)
        spent = {}
        for fam, name, lines in work:
            (room / "prog.txt").write_text("\n".join(lines) + "\n", encoding="utf-8",
                                           newline="\n")
            start = time.time()
            done = subprocess.run(
                [sys.executable, "-c",
                 "import sys;sys.path.insert(0,'.');import run_dur;"
                 "run_dur.run(open(sys.argv[1]).read())", str(room / "prog.txt")],
                cwd=room / "app", capture_output=True, text=True, timeout=2400)
            spent[fam] = spent.get(fam, 0.0) + time.time() - start
            if done.returncode:
                print("  %s %s FAILED %s" % (which, name, done.stderr.strip()[-200:]))
        print("%-11s %s  total %.1fs"
              % (which, "  ".join("%s %.1fs" % (k, v) for k, v in sorted(spent.items())),
                 sum(spent.values())), flush=True)
        shutil.rmtree(room)


if __name__ == "__main__":
    main()
