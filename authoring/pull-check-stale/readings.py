"""Wrong readings of the rebuild contract, as whole engines.

Each reading is the reference with one or two of its five files replaced by a version that
reads one rule the other way. They are reachable: every one is an engine a solver could
write from the brief and believe, not a mutation of a file nobody edits. The override is
appended to the reference source rather than spliced into it, so a reading cannot silently
fail to apply - and `_src` asserts the definition it overrides is still there, because a
rename that matched nothing once shipped as the reference (CLAUDE.md, reach-pair-sweep).

`tools/readingcheck.py <slug>` runs every reading against the enumerated set and, for any
the set does not separate, shrinks a counterexample out of the generated space.
"""

import importlib
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TASK = REPO / "tasks" / "pull-check-stale"
REFERENCE = str(TASK / "solution")
PRISTINE = TASK / "environment" / "app_src"

sys.path.insert(0, str(TASK / "tests"))
import cases          # noqa: E402
import gen            # noqa: E402


def _src(name, *needles):
    text = (Path(REFERENCE) / name).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise AssertionError("%s no longer defines %r - the reading would apply to "
                                 "nothing" % (name, needle))
    return text


WAKE = _src("wake.py", "def sound(", "def up(", "def open_round(")
STEP = _src("step.py", "def run_step(", "def _body(")
MARK = _src("mark.py", "def look_mark(", "def flat_holds(", "def pull_mark(")
KEEP = _src("keep.py", "def cut(")
HOLD = _src("hold.py", "class Hold")


def wake(body):
    return WAKE + "\n\n" + body


def step(body):
    return STEP + "\n\n" + body


def mark(body):
    return MARK + "\n\n" + body


READINGS = {

# The walk does not stop, so a pull observation after a failure brings that step up to
# date anyway.
"chk-all": {"wake.py": wake('''
def _sound(self, hold):
    good = True
    for m in hold.rec:
        if mark.is_pull(m):
            other = self.up(m[1])
            if m[2] == "!":
                if not other.dead:
                    good = False
            elif other.dead or other.value != m[2]:
                good = False
        elif not mark.flat_holds(m, self.keep):
            good = False
    return good


Wake.sound = _sound
''')},

# The cheap observations are taken first and the pulls afterwards, so the order the run
# made them is lost.
"chk-flat-first": {"wake.py": wake('''
def _sound(self, hold):
    for m in hold.rec:
        if not mark.is_pull(m) and not mark.flat_holds(m, self.keep):
            return False
    for m in hold.rec:
        if mark.is_pull(m):
            other = self.up(m[1])
            if m[2] == "!":
                if not other.dead:
                    return False
            elif other.dead or other.value != m[2]:
                return False
    return True


Wake.sound = _sound
''')},

# The verdict is a boolean for the round instead of a fact about the workspace.
"memo-round": {"wake.py": wake('''
def _open_round(self):
    self.board.open_round()
    self.fresh = set()


def _up(self, name):
    if name in self.path:
        i = self.path.index(name)
        raise Loop(self.path[i:] + [name])
    hold = self.board.get(name)
    if not hasattr(self, "fresh"):
        self.fresh = set()
    if hold.known and name in self.fresh:
        return hold
    self.path.append(name)
    try:
        if hold.known:
            if self.sound(hold):
                self.fresh.add(name)
                return hold
            if hold.ran:
                raise Stuck(name)
        out = run_step(self, name)
        self.fresh.add(name)
        return out
    finally:
        self.path.pop()


Wake.open_round = _open_round
Wake.up = _up
''')},

# A step that has already run and gone stale simply runs again.
"no-stuck": {"wake.py": wake('''
def _up(self, name):
    if name in self.path:
        i = self.path.index(name)
        raise Loop(self.path[i:] + [name])
    hold = self.board.get(name)
    if hold.known and hold.seen == self.keep.stamp:
        return hold
    self.path.append(name)
    try:
        if hold.known and self.sound(hold):
            hold.seen = self.keep.stamp
            return hold
        return run_step(self, name)
    finally:
        self.path.pop()


Wake.up = _up
''')},

# Being checked counts as having run, so an ordinary rebuild is reported as stuck.
"stuck-on-check": {"wake.py": wake('''
def _up(self, name):
    if name in self.path:
        i = self.path.index(name)
        raise Loop(self.path[i:] + [name])
    hold = self.board.get(name)
    if hold.known and hold.seen == self.keep.stamp:
        return hold
    self.path.append(name)
    try:
        if hold.known:
            if self.sound(hold):
                hold.seen = self.keep.stamp
                hold.ran = True
                return hold
            if hold.ran:
                raise Stuck(name)
        return run_step(self, name)
    finally:
        self.path.pop()


Wake.up = _up
''')},

# A look is recorded as if it had read the bytes.
"look-as-read": {"mark.py": mark('''
def look_mark(path, keep):
    return ("R", path, keep.digest(path))
''')},

# A look that found nothing is recorded but never disturbs anything.
"look-blind": {"mark.py": mark('''
def flat_holds(m, keep):
    kind = m[0]
    if kind == "R":
        return keep.digest(m[1]) == m[2]
    if kind == "L":
        if m[2] == "-":
            return True
        return keep.has(m[1])
    if kind == "O":
        return keep.digest(m[1]) == m[2]
    return True
''')},

# A run that dies keeps no record, so the step runs again every time it is asked for.
"fail-forget": {"step.py": step('''
_body_real = _body


def _body2(wake, name):
    out = _body_real(wake, name)
    if out.dead:
        out.rec = []
    return out


_body = _body2
''')},

# A step that died stays dead until something it succeeded on moves - which is never.
"fail-sticky": {"wake.py": wake('''
def _up(self, name):
    if name in self.path:
        i = self.path.index(name)
        raise Loop(self.path[i:] + [name])
    hold = self.board.get(name)
    if hold.known and hold.dead:
        return hold
    if hold.known and hold.seen == self.keep.stamp:
        return hold
    self.path.append(name)
    try:
        if hold.known:
            if self.sound(hold):
                hold.seen = self.keep.stamp
                return hold
            if hold.ran:
                raise Stuck(name)
        return run_step(self, name)
    finally:
        self.path.pop()


Wake.up = _up
''')},

# A re-run adds to the old record instead of replacing it.
"rec-merge": {"step.py": step('''
def _merge_run(wake, name):
    board = wake.board
    old = list(board.get(name).rec)
    wake.out.run(name)
    board.reset(name)
    try:
        hold = _body(wake, name)
    except Exception:
        board.reset(name)
        raise
    have = set((m[0], m[1]) for m in hold.rec)
    for m in old:
        if (m[0], m[1]) not in have:
            hold.rec.append(m)
    return hold


run_step = _merge_run
''')},

# A pull observation is treated as broken whenever the step it names ran this round.
"no-cutoff": {"wake.py": wake('''
def _sound(self, hold):
    for m in hold.rec:
        if mark.is_pull(m):
            other = self.up(m[1])
            if other.ran:
                return False
            if m[2] == "!":
                if not other.dead:
                    return False
            elif other.dead or other.value != m[2]:
                return False
        elif not mark.flat_holds(m, self.keep):
            return False
    return True


Wake.sound = _sound
''')},

# Reading a path some step writes brings that step up to date first.
"read-pulls": {"step.py": step('''
def _body3(wake, name):
    keep = wake.keep
    st = wake.plan.steps[name]
    hold = wake.board.get(name)
    vals = []
    for code, arg in st.ops:
        if code == "read":
            for maker in wake.plan.by_out.get(arg, []):
                if maker != name:
                    wake.up(maker)
            hold.rec.append(mark.read_mark(arg, keep))
            if not keep.has(arg):
                hold.dead = True
                hold.why = "missing %s" % arg
                break
            vals.append(keep.text(arg))
        elif code == "look":
            hold.rec.append(mark.look_mark(arg, keep))
        elif code == "pull":
            other = wake.up(arg)
            hold.rec.append(mark.pull_mark(arg, other))
            if other.dead:
                hold.dead = True
                hold.why = "via %s" % arg
                break
            vals.append(other.value)
        else:
            hold.value = dig.mix(vals) if arg == "*" else arg
            break
    hold.known = True
    if not hold.dead:
        keep.put(st.out, hold.value)
        hold.rec.append(mark.out_mark(st.out, keep))
    hold.ran = True
    hold.seen = keep.stamp
    return hold


_body = _body3
''')},

# What a run left at its own output path is not observed.
"no-out-mark": {"mark.py": mark('''
def flat_holds(m, keep):
    kind = m[0]
    if kind == "R":
        return keep.digest(m[1]) == m[2]
    if kind == "L":
        return keep.has(m[1]) == (m[2] == "+")
    return True
''')},

# The loop chain starts at the step the request named.
"loop-from-root": {"wake.py": wake('''
def _up(self, name):
    if name in self.path:
        raise Loop(self.path + [name])
    hold = self.board.get(name)
    if hold.known and hold.seen == self.keep.stamp:
        return hold
    self.path.append(name)
    try:
        if hold.known:
            if self.sound(hold):
                hold.seen = self.keep.stamp
                return hold
            if hold.ran:
                raise Stuck(name)
        return run_step(self, name)
    finally:
        self.path.pop()


Wake.up = _up
''')},

# The chain does not close on the step it repeats.
"loop-no-close": {"wake.py": wake('''
def _up(self, name):
    if name in self.path:
        i = self.path.index(name)
        raise Loop(self.path[i:])
    hold = self.board.get(name)
    if hold.known and hold.seen == self.keep.stamp:
        return hold
    self.path.append(name)
    try:
        if hold.known:
            if self.sound(hold):
                hold.seen = self.keep.stamp
                return hold
            if hold.ran:
                raise Stuck(name)
        return run_step(self, name)
    finally:
        self.path.pop()


Wake.up = _up
''')},

# The reason travels up from wherever the failure started.
"via-inner": {"step.py": step('''
def _body4(wake, name):
    keep = wake.keep
    st = wake.plan.steps[name]
    hold = wake.board.get(name)
    vals = []
    for code, arg in st.ops:
        if code == "read":
            hold.rec.append(mark.read_mark(arg, keep))
            if not keep.has(arg):
                hold.dead = True
                hold.why = "missing %s" % arg
                break
            vals.append(keep.text(arg))
        elif code == "look":
            hold.rec.append(mark.look_mark(arg, keep))
        elif code == "pull":
            other = wake.up(arg)
            hold.rec.append(mark.pull_mark(arg, other))
            if other.dead:
                hold.dead = True
                hold.why = other.why
                break
            vals.append(other.value)
        else:
            hold.value = dig.mix(vals) if arg == "*" else arg
            break
    hold.known = True
    if not hold.dead:
        keep.put(st.out, hold.value)
        hold.rec.append(mark.out_mark(st.out, keep))
    hold.ran = True
    hold.seen = keep.stamp
    return hold


_body = _body4
''')},

# A dead pull is recorded with the reason, so it only holds while the reason is the same.
"dead-reason-match": {
    "mark.py": mark('''
def pull_mark(name, hold):
    if hold.dead:
        return ("P", name, "!%s" % hold.why)
    return ("P", name, hold.value)
'''),
    "wake.py": wake('''
def _sound(self, hold):
    for m in hold.rec:
        if mark.is_pull(m):
            other = self.up(m[1])
            if str(m[2]).startswith("!"):
                if not other.dead or ("!%s" % other.why) != m[2]:
                    return False
            elif other.dead or other.value != m[2]:
                return False
        elif not mark.flat_holds(m, self.keep):
            return False
    return True


Wake.sound = _sound
'''),
},

# The run line is printed once the run is over.
"run-line-after": {"step.py": step('''
def _late_run(wake, name):
    board = wake.board
    board.reset(name)
    try:
        hold = _body(wake, name)
    except Exception:
        board.reset(name)
        wake.out.run(name)
        raise
    wake.out.run(name)
    return hold


run_step = _late_run
''')},

# Removing a path empties it instead of taking it away.
"cut-tombstone": {"keep.py": KEEP + '''

def _cut(self, path):
    if path not in self.body:
        return
    if self.body[path] == "":
        return
    self.body[path] = ""
    self.dgc.pop(path, None)
    self.stamp += 1


Keep.cut = _cut
'''},

# The value of `emit *` is taken from what was read, not from what was pulled.
"emit-reads-only": {"step.py": step('''
def _body5(wake, name):
    keep = wake.keep
    st = wake.plan.steps[name]
    hold = wake.board.get(name)
    vals = []
    for code, arg in st.ops:
        if code == "read":
            hold.rec.append(mark.read_mark(arg, keep))
            if not keep.has(arg):
                hold.dead = True
                hold.why = "missing %s" % arg
                break
            vals.append(keep.text(arg))
        elif code == "look":
            hold.rec.append(mark.look_mark(arg, keep))
        elif code == "pull":
            other = wake.up(arg)
            hold.rec.append(mark.pull_mark(arg, other))
            if other.dead:
                hold.dead = True
                hold.why = "via %s" % arg
                break
        else:
            hold.value = dig.mix(vals) if arg == "*" else arg
            break
    hold.known = True
    if not hold.dead:
        keep.put(st.out, hold.value)
        hold.rec.append(mark.out_mark(st.out, keep))
    hold.ran = True
    hold.seen = keep.stamp
    return hold


_body = _body5
''')},

# The read that killed the run is not recorded.
"miss-no-mark": {"step.py": step('''
def _body6(wake, name):
    keep = wake.keep
    st = wake.plan.steps[name]
    hold = wake.board.get(name)
    vals = []
    for code, arg in st.ops:
        if code == "read":
            if not keep.has(arg):
                hold.dead = True
                hold.why = "missing %s" % arg
                break
            hold.rec.append(mark.read_mark(arg, keep))
            vals.append(keep.text(arg))
        elif code == "look":
            hold.rec.append(mark.look_mark(arg, keep))
        elif code == "pull":
            other = wake.up(arg)
            hold.rec.append(mark.pull_mark(arg, other))
            if other.dead:
                hold.dead = True
                hold.why = "via %s" % arg
                break
            vals.append(other.value)
        else:
            hold.value = dig.mix(vals) if arg == "*" else arg
            break
    hold.known = True
    if not hold.dead:
        keep.put(st.out, hold.value)
        hold.rec.append(mark.out_mark(st.out, keep))
    hold.ran = True
    hold.seen = keep.stamp
    return hold


_body = _body6
''')},
}


_TREES = {}


def _tree(policy):
    policy = str(policy)
    if policy not in _TREES:
        root = Path(tempfile.mkdtemp(prefix="pcs-tree-"))
        shutil.copytree(PRISTINE, root / "app")
        for p in Path(policy).iterdir():
            if p.suffix == ".py":
                shutil.copyfile(p, root / "app" / "eng" / p.name)
        _TREES[policy] = root / "app"
    return _TREES[policy]


def run(policy, text):
    """Drive one program under one engine and return the trace it prints."""
    root = _tree(policy)
    prog = root / "_case.txt"
    prog.write_text(text.strip("\n") + "\n", encoding="utf-8", newline="\n")
    for name in [m for m in sys.modules if m == "run_eng" or m.startswith("eng")]:
        del sys.modules[name]
    sys.path.insert(0, str(root))
    try:
        run_eng = importlib.import_module("run_eng")
        return run_eng.build(str(prog))
    finally:
        sys.path.remove(str(root))


def enumerated():
    return cases.programs()


def generated(n):
    per = max(1, n // (len(gen.FAMILIES) + 1))
    out = []
    for seed in ("r1", "r2", "r3"):
        out.extend(gen.programs(seed, per))
        if len(out) >= n:
            break
    return out[:n]


def reductions(text):
    """Structure-aware shrinking: drop a step with every op and pull that names it, or
    drop one round, rather than one line at a time."""
    lines = text.split("\n")
    steps = [f[1] for f in (line.split() for line in lines) if f and f[0] == "step"]
    for name in steps:
        keep = []
        for line in lines:
            f = line.split()
            if not f:
                continue
            if f[0] == "step" and f[1] == name:
                continue
            if f[0] == "op" and f[1] == name:
                continue
            if f[0] == "op" and len(f) == 4 and f[2] == "pull" and f[3] == name:
                continue
            if f[0] == "want" and f[1] == name:
                continue
            keep.append(line)
        yield "\n".join(keep)
    starts = [i for i, line in enumerate(lines) if line.split()[:1] == ["round"]]
    for k, i in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        yield "\n".join(lines[:i] + lines[end:])
    for i in range(len(lines) - 1, -1, -1):
        yield "\n".join(lines[:i] + lines[i + 1:])


def policy_dir_for(files):
    """The reference with one reading's files swapped in - the same tree
    tools/readingcheck.py builds, reused by authoring/ablate.py."""
    import os
    d = Path(tempfile.mkdtemp(prefix="reading-"))
    for p in Path(REFERENCE).iterdir():
        if p.suffix == ".py":
            shutil.copyfile(p, d / p.name)
    for name, src in files.items():
        (d / name).write_text(src, encoding="utf-8", newline="\n")
    os.environ.setdefault("PCS_READING_DIRS", "")
    return d
