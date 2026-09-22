"""Independent model of the rebuild service.

Written apart from `solution/`, and deliberately in a different shape: the scheduler here
is an explicit trampoline over per-step generators that suspend at every pull, instead of
the reference's direct recursion, and the state is a set of parallel dicts instead of a
per-step object. Nothing is shared between the two beyond the specification, so agreement
between them over the graded set is evidence about the specification rather than about one
implementation's habits.

The specification, in the order the engine applies it:

* A record is the ordered list of the observations one run made. Four kinds: a read of a
  path (its digest, or `-` when the path was not there), a look at a path (present or
  absent, never the bytes), a pull of a step (its value, or `!` when that step was dead),
  and the output a successful run wrote.
* A step already on the live pull stack is a loop. The chain runs from where that step
  first appears on the stack, through the top, and back to it.
* A step whose last verdict was taken at the version the workspace still carries is up to
  date with no further work.
* Otherwise the record is walked in order and the walk stops at the first observation that
  no longer holds. Walking a pull observation means bringing that step up to date, so the
  walk runs steps; observations past the first failure are neither walked nor run.
* A record that still holds leaves the step alone. A record that does not means the step
  runs - unless it has already run this round, which is `stuck`.
* A run dies on a read of an absent path (`missing <path>`) or on a pull of a dead step
  (`via <step>`), keeping the record it had built including the observation it died on. A
  run cut short by a loop or a stuck below it leaves nothing: the step counts as never run.
* A successful run writes its value to its output path. A write only counts as a change to
  the workspace when the bytes actually move, which is what leaves earlier verdicts
  standing when a re-run emits what it emitted before.
"""

import hashlib
import re

WORD = re.compile(r"^[a-z0-9_.]+$")


class Bad(Exception):
    pass


class Ring(Exception):
    def __init__(self, chain):
        Exception.__init__(self)
        self.chain = chain


class Halt(Exception):
    def __init__(self, name):
        Exception.__init__(self)
        self.name = name


def of(text):
    return hashlib.blake2s(text.encode("utf-8"), digest_size=4).hexdigest()


def mix(vals):
    h = hashlib.blake2s(digest_size=3)
    for v in vals:
        h.update(v.encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()


# --- program text -------------------------------------------------------------------

def parse(text):
    seeds, steps, order, rounds, outs = [], {}, [], [], {}
    cur = None
    for n, raw in enumerate(text.splitlines(), 1):
        f = raw.split()
        if not f:
            continue
        try:
            if f[0] == "seed" and len(f) == 3:
                seeds.append((tok(f[1]), tok(f[2])))
            elif f[0] == "step" and len(f) == 3:
                if f[1] in steps:
                    raise Bad("step %s twice" % f[1])
                steps[tok(f[1])] = [tok(f[2]), []]
                order.append(f[1])
                outs.setdefault(f[2], []).append(f[1])
            elif f[0] == "op" and len(f) == 4:
                if f[1] not in steps:
                    raise Bad("op before step %s" % f[1])
                if f[2] not in ("read", "look", "pull", "emit"):
                    raise Bad("bad op %s" % f[2])
                if f[2] != "emit" or f[3] != "*":
                    tok(f[3])
                steps[f[1]][1].append((f[2], f[3]))
            elif f[0] == "round" and len(f) == 1:
                cur = []
                rounds.append(cur)
            elif f[0] in ("put", "cut", "want"):
                if cur is None:
                    raise Bad("%s outside a round" % f[0])
                if f[0] == "put" and len(f) == 3:
                    cur.append(("put", tok(f[1]), tok(f[2])))
                elif f[0] == "cut" and len(f) == 2:
                    cur.append(("cut", tok(f[1])))
                elif f[0] == "want" and len(f) == 2:
                    cur.append(("want", tok(f[1])))
                else:
                    raise Bad("bad %s" % f[0])
            else:
                raise Bad("bad line %r" % raw)
        except Bad as exc:
            raise Bad("line %d: %s" % (n, exc))
    for name in order:
        ops = steps[name][1]
        if not ops or ops[-1][0] != "emit":
            raise Bad("step %s does not end with emit" % name)
        if sum(1 for c, _ in ops if c == "emit") != 1:
            raise Bad("step %s emits more than once" % name)
    for rd in rounds:
        for d in rd:
            if d[0] == "want" and d[1] not in steps:
                raise Bad("want %s is not a step" % d[1])
    for name in order:
        for code, arg in steps[name][1]:
            if code == "pull" and arg not in steps:
                raise Bad("%s pulls %s which is not a step" % (name, arg))
    return {"seeds": seeds, "steps": steps, "order": order, "rounds": rounds, "outs": outs}


def tok(t):
    if not WORD.match(t):
        raise Bad("bad token %r" % t)
    return t


# --- the engine ---------------------------------------------------------------------

class Mdl:
    def __init__(self, prog):
        self.prog = prog
        self.files = {}
        self.dgc = {}
        self.ver = 0
        self.note = {n: [] for n in prog["order"]}
        self.fact = {n: None for n in prog["order"]}
        self.at = {n: -1 for n in prog["order"]}
        self.fired = set()
        self.out = []

    # workspace ----------------------------------------------------------------
    def write(self, path, word):
        if path in self.files and self.files[path] == word:
            return
        self.files[path] = word
        self.dgc.pop(path, None)
        self.ver += 1

    def erase(self, path):
        if path not in self.files:
            return
        del self.files[path]
        self.dgc.pop(path, None)
        self.ver += 1

    def hash_of(self, path):
        if path not in self.files:
            return "-"
        if path not in self.dgc:
            self.dgc[path] = of(self.files[path])
        return self.dgc[path]

    def flat(self, ob):
        kind, where, what = ob
        if kind in ("R", "O"):
            return self.hash_of(where) == what
        return (where in self.files) == (what == "+")

    def wipe(self, name):
        self.note[name] = []
        self.fact[name] = None
        self.at[name] = -1

    # one step, as a coroutine that suspends on every pull ---------------------
    def serve(self, name):
        old = self.fact[name]
        if old is not None:
            stale = False
            for ob in self.note[name]:
                if ob[0] == "P":
                    got = yield ob[1]
                    if ob[2] == "!":
                        fine = got[0] == "bad"
                    else:
                        fine = got[0] == "ok" and got[1] == ob[2]
                else:
                    fine = self.flat(ob)
                if not fine:
                    stale = True
                    break
            if not stale:
                self.at[name] = self.ver
                return old
            if name in self.fired:
                raise Halt(name)
        self.out.append("run " + name)
        self.wipe(name)
        try:
            res = yield from self.work(name)
        except BaseException:
            self.wipe(name)
            raise
        return res

    def work(self, name):
        where, ops = self.prog["steps"][name]
        seen = self.note[name]
        vals = []
        fact = None
        for code, arg in ops:
            if code == "read":
                seen.append(("R", arg, self.hash_of(arg)))
                if arg not in self.files:
                    fact = ("bad", "missing %s" % arg)
                    break
                vals.append(self.files[arg])
            elif code == "look":
                seen.append(("L", arg, "+" if arg in self.files else "-"))
            elif code == "pull":
                got = yield arg
                if got[0] == "bad":
                    seen.append(("P", arg, "!"))
                    fact = ("bad", "via %s" % arg)
                    break
                seen.append(("P", arg, got[1]))
                vals.append(got[1])
            else:
                fact = ("ok", mix(vals) if arg == "*" else arg)
                break
        self.fact[name] = fact
        if fact[0] == "ok":
            self.write(where, fact[1])
            seen.append(("O", where, self.hash_of(where)))
        self.fired.add(name)
        self.at[name] = self.ver
        return fact

    # trampoline ---------------------------------------------------------------
    def bring(self, top):
        live = []
        frames = []
        hit = self.settled(top)
        if hit is not None:
            return hit
        frames.append(self.serve(top))
        live.append(top)
        pass_in = None
        try:
            while True:
                try:
                    want = frames[-1].send(pass_in)
                except StopIteration as done:
                    frames.pop()
                    live.pop()
                    pass_in = done.value
                    if not frames:
                        return pass_in
                    continue
                if want in live:
                    raise Ring(live[live.index(want):] + [want])
                hit = self.settled(want)
                if hit is not None:
                    pass_in = hit
                    continue
                frames.append(self.serve(want))
                live.append(want)
                pass_in = None
        except BaseException:
            while frames:
                frames.pop().close()
            raise

    def settled(self, name):
        if self.fact[name] is not None and self.at[name] == self.ver:
            return self.fact[name]
        return None

    # whole program -------------------------------------------------------------
    def play(self):
        for path, word in self.prog["seeds"]:
            self.write(path, word)
        for n, rd in enumerate(self.prog["rounds"], 1):
            self.out.append("round %d" % n)
            self.fired = set()
            for d in rd:
                if d[0] == "put":
                    self.write(d[1], d[2])
                elif d[0] == "cut":
                    self.erase(d[1])
                else:
                    self.ask(d[1])
        return "\n".join(self.out)

    def ask(self, name):
        try:
            fact = self.bring(name)
        except Ring as exc:
            self.out.append("loop %s" % " ".join(exc.chain))
            return
        except Halt as exc:
            self.out.append("stuck %s" % exc.name)
            return
        if fact[0] == "ok":
            self.out.append("ok %s %s" % (name, fact[1]))
        else:
            self.out.append("err %s %s" % (name, fact[1]))


def trace(text):
    return Mdl(parse(text)).play()


def trace_file(path):
    with open(path, "r", encoding="utf-8") as fh:
        return trace(fh.read())


def expect(text):
    """The trace, as a list of lines - the shape the worker's record is compared with."""
    return trace(text).split("\n")
