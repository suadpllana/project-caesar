#!/bin/bash
# removing a path empties it instead of taking it away
set -euo pipefail

cat > /app/eng/keep.py <<'PCSEOF'
from eng import dig


class Keep:
    """The workspace.

    `stamp` is the number of changes the workspace has taken. It advances only when a
    path's bytes actually move, which is what makes a verdict taken at a stamp still
    worth something while the stamp is unchanged, and what makes a re-run that emits the
    same value leave every earlier verdict standing.

    Digests are cached per path and dropped whenever the path changes, so a check costs a
    dict lookup rather than a rehash. That is sound for the same reason: bytes only ever
    change through `put` and `cut`.
    """

    def __init__(self):
        self.body = {}
        self.dgc = {}
        self.stamp = 0

    def has(self, path):
        return path in self.body

    def text(self, path):
        return self.body.get(path, "")

    def digest(self, path):
        if path not in self.body:
            return "-"
        d = self.dgc.get(path)
        if d is None:
            d = dig.of(self.body[path])
            self.dgc[path] = d
        return d

    def put(self, path, word):
        if self.body.get(path) == word and path in self.body:
            return
        self.body[path] = word
        self.dgc.pop(path, None)
        self.stamp += 1

    def cut(self, path):
        if path not in self.body:
            return
        del self.body[path]
        self.dgc.pop(path, None)
        self.stamp += 1


def _cut(self, path):
    if path not in self.body:
        return
    if self.body[path] == "":
        return
    self.body[path] = ""
    self.dgc.pop(path, None)
    self.stamp += 1


Keep.cut = _cut
PCSEOF

cat > /app/eng/mark.py <<'PCSEOF'
def read_mark(path, keep):
    """A read observes the bytes: the digest, or `-` when the path was not there."""
    return ("R", path, keep.digest(path))


def look_mark(path, keep):
    """A look observes presence only, so a rewrite of the same path does not disturb it."""
    return ("L", path, "+" if keep.has(path) else "-")


def pull_mark(name, hold):
    """A pull observes the value, or that the step was dead - never the reason."""
    if hold.dead:
        return ("P", name, "!")
    return ("P", name, hold.value)


def out_mark(path, keep):
    """A successful run observes the bytes it left at its own output path."""
    return ("O", path, keep.digest(path))


def is_pull(m):
    return m[0] == "P"


def flat_holds(m, keep):
    """Whether an observation that needs only the workspace still holds."""
    kind = m[0]
    if kind == "R":
        return keep.digest(m[1]) == m[2]
    if kind == "L":
        return keep.has(m[1]) == (m[2] == "+")
    if kind == "O":
        return keep.digest(m[1]) == m[2]
    return True
PCSEOF

cat > /app/eng/hold.py <<'PCSEOF'
class Loop(Exception):
    """A pull that reached a step already on the live stack."""

    def __init__(self, chain):
        Exception.__init__(self)
        self.chain = chain


class Stuck(Exception):
    """A step that has already run this round and has since gone stale."""

    def __init__(self, name):
        Exception.__init__(self)
        self.name = name


class Hold:
    """What the engine remembers about one step.

    `seen` is the workspace stamp at which the record was last found to hold. `ran` says
    the step has actually run this round, which is a different fact from having been
    checked: a step that was only checked and has since gone stale runs, a step that ran
    and has since gone stale is `stuck`.
    """

    def __init__(self, name):
        self.name = name
        self.rec = []
        self.value = None
        self.why = None
        self.dead = False
        self.known = False
        self.seen = -1
        self.ran = False


class Board:
    def __init__(self, p):
        self.holds = {}
        for name in p.order:
            self.holds[name] = Hold(name)

    def get(self, name):
        return self.holds[name]

    def open_round(self):
        for h in self.holds.values():
            h.ran = False

    def reset(self, name):
        """Undo a run that was cut short, so the step is as if it had never run."""
        h = self.holds[name]
        h.rec = []
        h.value = None
        h.why = None
        h.dead = False
        h.known = False
        h.seen = -1
PCSEOF

cat > /app/eng/step.py <<'PCSEOF'
from eng import dig
from eng import mark


def run_step(wake, name):
    """Run one step, building its record as the run makes each observation.

    A run that is cut short by a loop or a stuck below it leaves nothing behind: the hold
    is reset, so the step counts as never having run. A run that dies on its own - a read
    of a path that is not there, or a pull of a dead step - keeps the record it built,
    ending with the observation it died on. That partial record is what brings the step
    back to life later: the absence it recorded is exactly what stops holding when the
    path appears.
    """
    board = wake.board
    wake.out.run(name)
    board.reset(name)
    try:
        return _body(wake, name)
    except Exception:
        board.reset(name)
        raise


def _body(wake, name):
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
PCSEOF

cat > /app/eng/wake.py <<'PCSEOF'
from eng import mark
from eng.hold import Loop, Stuck
from eng.step import run_step


class Wake:
    """Bringing steps up to date.

    Three things decide what happens to a request, and they are checked in this order.
    A step already on the live stack is a loop, and the chain runs from where that step
    first appears. A step whose verdict was taken at the stamp the workspace still
    carries needs nothing: nothing has changed since, so the verdict still holds - that
    is what keeps the diamond programs linear. Otherwise the record is walked in the
    order the run made it, stopping at the first observation that no longer holds;
    walking a pull observation means bringing that step up to date, so the walk is what
    runs steps, and observations past the first failure are neither checked nor run.

    Only then does the record's failure mean anything: a step that has merely been
    checked this round runs, a step that has already run this round is `stuck`.
    """

    def __init__(self, p, keep, board, out):
        self.plan = p
        self.keep = keep
        self.board = board
        self.out = out
        self.path = []

    def open_round(self):
        self.board.open_round()

    def request(self, name):
        self.path = []
        try:
            hold = self.up(name)
        except Loop as exc:
            self.out.loop(exc.chain)
            return
        except Stuck as exc:
            self.out.stuck(exc.name)
            return
        if hold.dead:
            self.out.err(name, hold.why)
        else:
            self.out.ok(name, hold.value)

    def up(self, name):
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
                    return hold
                if hold.ran:
                    raise Stuck(name)
            return run_step(self, name)
        finally:
            self.path.pop()

    def sound(self, hold):
        for m in hold.rec:
            if mark.is_pull(m):
                other = self.up(m[1])
                if m[2] == "!":
                    if not other.dead:
                        return False
                elif other.dead or other.value != m[2]:
                    return False
            elif not mark.flat_holds(m, self.keep):
                return False
        return True
PCSEOF
