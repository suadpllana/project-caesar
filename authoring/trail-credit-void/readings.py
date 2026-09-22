"""Every reading of the brief a competent solver might hold, written down and run.

Coverage on paper is not coverage: the question is whether a *specific* plausible-but-wrong
reading survives the enumerated set. Each reading below is built by patching exactly one file
of the reference, and every patch asserts that it fired, because a substitution that matched
nothing produces a variant identical to the reference and reports "equivalent" for the wrong
reason (CLAUDE.md, 2026-09-06).

Two of these are not inventions. `rearm-on-touch` is the bug the author's own first reference
carried: driving candidates off the keys a step wrote misses a goal shut while its predicate
already fails, because no key it reads has to change for it to re-arm. `credit-recompute`,
`bar-state`, `err-keeps`, `bud-per-step`, `close-keeps`, `rep-count`, `up-strict` and
`off-zero` are what the shipped engine does, and whatever the shipped engine does is a reading
somebody keeps.

One candidate was dropped rather than kept: refreshing the previous-observation values from a
copy of the whole store is not a wrong reading at all, only a slower way of holding the same
thing, and it is carried as the `slow-snap` correct-but-too-slow variant instead.
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, _model = lab.sealed()

REFERENCE = str(lab.SOL)

_TREES = {}


def sub(name, old, new, count=1):
    """The reference file `name` with `old` replaced, failing loudly if it was not there."""
    text = (lab.SOL / name).read_text(encoding="utf-8")
    got = text.count(old)
    if got != count:
        raise AssertionError("%s: pattern found %d times, wanted %d" % (name, got, count))
    return {name: text.replace(old, new)}


ACTIONS = """            if op == "put":
                store.put(key, val)
            else:
                store.cut(key)
            used += 1"""

CREDIT = """    def credit(self, store, moved, delta):
        state = self.state
        ready = self.ready
        goals = self.goals
        won = []
        for gid in self.near(moved):
            here = state[gid]
            if here == SHUT:
                if not pred.holds(goals[gid], store):
                    state[gid] = OPEN
            elif here == OPEN and ready[gid] == 0 and pred.holds(goals[gid], store):
                state[gid] = HELD
                delta[gid] = delta.get(gid, 0) + 1
                won.append(gid)
        return won"""

FIRE = """def fire(book, bar, delta):
    state = book.state
    lost = []
    for gid in cone(book, bar.goal):
        if state[gid] == bk.HELD:
            state[gid] = bk.OPEN
            delta[gid] = delta.get(gid, 0) - 1
            lost.append(gid)
    book.shut(bar.goal)
    return lost"""


READINGS = {
    # --- when an observation happens ---------------------------------------------------
    "obs-per-action": sub(
        "ep.py", ACTIONS,
        ACTIONS + "\n            watched(book, watch, store, out, store.take())"),
    "obs-err-too": sub(
        "ep.py",
        """        if short or not done:
            store.undo(here)""",
        """        if short or not done:
            if not short:
                watched(book, watch, store, out, store.take())
            store.undo(here)"""),

    # --- what may be credited there ----------------------------------------------------
    "pre-same-obs": sub(
        "book.py", CREDIT,
        """    def credit(self, store, moved, delta):
        state = self.state
        ready = self.ready
        goals = self.goals
        won = []
        again = True
        while again:
            again = False
            for gid in self.near(moved) if not won else range(len(goals)):
                here = state[gid]
                if here == SHUT:
                    if not pred.holds(goals[gid], store):
                        state[gid] = OPEN
                elif here == OPEN and ready[gid] == 0 and pred.holds(goals[gid], store):
                    state[gid] = HELD
                    delta[gid] = delta.get(gid, 0) + 1
                    self.settle({gid: 1})
                    won.append(gid)
                    again = True
        won.sort()
        return won"""),
    "credit-recompute": sub(
        "book.py", CREDIT,
        CREDIT.replace("""        won = []
        for gid in self.near(moved):""",
                       """        won = []
        for gid in range(len(goals)):
            if state[gid] == HELD and not pred.holds(goals[gid], store):
                state[gid] = OPEN
                delta[gid] = delta.get(gid, 0) - 1
        for gid in self.near(moved):""")),
    "rearm-now": sub(
        "book.py", CREDIT,
        CREDIT.replace("""            if here == SHUT:
                if not pred.holds(goals[gid], store):
                    state[gid] = OPEN
            elif here == OPEN and""",
                       """            if here == SHUT:
                state[gid] = OPEN
                here = OPEN
            if here == OPEN and""")),
    "rearm-on-touch": sub(
        "book.py",
        """    def shut(self, gid):
        self.state[gid] = SHUT
        self.queue.add(gid)""",
        """    def shut(self, gid):
        self.state[gid] = SHUT"""),

    # --- what a violation takes ---------------------------------------------------------
    "void-named-only": sub(
        "void.py", FIRE,
        """def fire(book, bar, delta):
    state = book.state
    lost = []
    if state[bar.goal] == bk.HELD:
        delta[bar.goal] = delta.get(bar.goal, 0) - 1
        lost.append(bar.goal)
    book.shut(bar.goal)
    return lost"""),
    "void-cone-shut": sub(
        "void.py", FIRE,
        """def fire(book, bar, delta):
    state = book.state
    lost = []
    for gid in cone(book, bar.goal):
        if state[gid] == bk.HELD:
            delta[gid] = delta.get(gid, 0) - 1
            lost.append(gid)
        book.shut(gid)
    return lost"""),
    "void-walk-order": sub(
        "void.py",
        """def cone(book, gid):
    seen = {gid}
    stack = [gid]
    while stack:
        here = stack.pop()
        for down in book.dep[here]:
            if down not in seen:
                seen.add(down)
                stack.append(down)
    return sorted(seen)""",
        """def cone(book, gid):
    seen = {gid}
    order = [gid]
    stack = [gid]
    while stack:
        here = stack.pop()
        for down in book.dep[here]:
            if down not in seen:
                seen.add(down)
                order.append(down)
                stack.append(down)
    return order"""),
    "void-uncredited-skip": sub(
        "void.py", FIRE,
        FIRE.replace("    book.shut(bar.goal)",
                     "    if lost:\n        book.shut(bar.goal)")),

    # --- the order of the two halves ------------------------------------------------------
    "bars-first": sub(
        "ep.py",
        """    delta = {}
    for gid in book.credit(store, moved, delta):
        out.line("mark %d" % gid)
    for bar in watch.near(moved):
        if watch.fires(bar, store):
            out.line("fire %d" % bar.bid)
            for gid in void.fire(book, bar, delta):
                out.line("void %d" % gid)""",
        """    delta = {}
    for bar in watch.near(moved):
        if watch.fires(bar, store):
            out.line("fire %d" % bar.bid)
            for gid in void.fire(book, bar, delta):
                out.line("void %d" % gid)
    for gid in book.credit(store, moved, delta):
        out.line("mark %d" % gid)"""),

    # --- what a violation is ----------------------------------------------------------------
    "bar-state": sub(
        "obs.py",
        """        if kind == "lost":
            return was is not None and now is None
        if kind == "gain":
            return was is None and now is not None
        return was is not None and now is not None and now < was""",
        """        if kind == "lost":
            return now is None
        if kind == "gain":
            return now is not None
        return was != now"""),
    "bar-back-any": sub(
        "obs.py",
        "        return was is not None and now is not None and now < was",
        "        return was is not None and now is not None and now != was"),

    # --- the records around a step -----------------------------------------------------------
    "err-keeps": sub(
        "ep.py",
        """        if short or not done:
            store.undo(here)""",
        """        if short or not done:
            if short:
                store.undo(here)"""),

    # --- the budget ----------------------------------------------------------------------------
    "bud-per-step": sub(
        "ep.py",
        """        for op, key, val in actions:
            if used >= cfg.budget:
                short = True
                break""",
        """        if used >= cfg.budget:
            short = True
            actions = ()
        for op, key, val in actions:"""),
    "bud-spares-failed": sub(
        "ep.py",
        """        if short or not done:
            store.undo(here)""",
        """        if short or not done:
            if not short:
                used -= len(actions)
            store.undo(here)"""),

    # --- closing an episode ----------------------------------------------------------------------
    "close-keeps": sub(
        "ep.py",
        """    if closed:
        store.undo(start)""",
        """    if closed:
        pass"""),
    "close-loses-credit": sub(
        "ep.py",
        """    if closed:
        store.undo(start)""",
        """    if closed:
        store.undo(start)
        book.state = [0] * len(one.goals)"""),

    # --- the predicates ----------------------------------------------------------------------------
    "up-strict": sub(
        "pred.py",
        "        return got is not None and got >= goal.val",
        "        return got is not None and got > goal.val"),
    "off-zero": sub(
        "pred.py",
        "    return got is None",
        "    return not got"),

    # --- the report ----------------------------------------------------------------------------------
    "rep-count": sub(
        "tally.py",
        "    got = sum(goal.weight for goal in one.goals if book.held(goal.gid))",
        "    got = sum(1 for goal in one.goals if book.held(goal.gid))"),
    "rep-full-any": sub(
        "tally.py",
        "        if got == whole:",
        "        if got:"),
}


def run(policy, text):
    """Drive one trail under one directory of the seven files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    return lab.run_text(here, text)


def enumerated():
    return [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]


def generated(n):
    out = []
    small = [f for f, big in gen.FAMILIES if not big]
    per = max(1, n // len(small))
    for fam in small:
        for turn in range(per):
            rnd = random.Random("readingcheck|%s|%d" % (fam, turn))
            out.append(("%s-%d" % (fam, turn),
                        "\n".join(gen.MAKERS[fam](rnd)) + "\n"))
    return out[:n]


def reductions(text):
    """Structure-aware shrinking: drop a whole step, a goal, a bar or a seeded record.

    A trail is lines, but a step is a region: dropping a `step` line on its own leaves its
    actions attached to the step before it, which is a different trail rather than a smaller
    one, so the line-only shrinker plateaus. Dropping a goal also has to drop every bar and
    prerequisite that names it and renumber what is left, or the trail stops parsing.
    """
    lines = text.strip("\n").split("\n")
    heads = [i for i, one in enumerate(lines) if one.startswith("step")]
    for i in heads:
        j = i + 1
        while j < len(lines) and lines[j].split()[0] not in ("step", "ep"):
            j += 1
        yield "\n".join(lines[:i] + lines[j:])
    for i, one in enumerate(lines):
        if one.startswith(("rec ", "bar ", "put ", "cut ")):
            yield "\n".join(lines[:i] + lines[i + 1:])
    for i, one in enumerate(lines):
        if one.startswith("bar "):
            kept = [x for k, x in enumerate(lines) if k != i]
            out, bid = [], 0
            for x in kept:
                if x.startswith("bar "):
                    part = x.split()
                    part[1] = str(bid)
                    bid += 1
                    x = " ".join(part)
                out.append(x)
            yield "\n".join(out)
