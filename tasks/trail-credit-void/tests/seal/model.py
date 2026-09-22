"""The sealed model: what a trail is supposed to print.

Written apart from the reference under `solution/`, against the same contract, and holding
every piece of state differently so that the shape of an implementation is visibly not what is
graded. The reference keeps goal states in an integer array, the count of prerequisites still
owed in a parallel array, and walks dependants from a stack; this keeps two sets, records the
observation index at which each goal was credited and compares that index directly, and walks
dependants breadth first from a deque. Both have to agree on every graded trail, and the grader
re-checks this model against the frozen answers before it judges anything.

The rules, in the order an observation applies them:

  * an observation happens at the end of a step that ended ok, and at the start of an episode,
    where it only records the values the next observation is compared against;
  * goals are taken in ascending id, once: a shut goal whose predicate fails opens, and an open
    goal whose predicate holds is credited when every prerequisite was credited at a strictly
    earlier observation of this episode;
  * credit then settles - it survives the predicate going false;
  * bars are then taken in ascending id against the pair (previous observation, this one); a
    bar that holds fires, shuts the goal it names and strips the credit of that goal and of
    every goal standing on it, directly or through others.
"""
import spec
from collections import deque

MISS = object()


class Rec:
    """The records, with a log that undoes exactly what a span wrote."""

    __slots__ = ("val", "log", "moved")

    def __init__(self):
        self.val = {}
        self.log = []
        self.moved = set()

    def mark(self):
        return len(self.log)

    def put(self, key, value):
        self.log.append((key, self.val.get(key, MISS)))
        self.val[key] = value
        self.moved.add(key)

    def cut(self, key):
        self.log.append((key, self.val.get(key, MISS)))
        self.val.pop(key, None)
        self.moved.add(key)

    def back_to(self, mark):
        while len(self.log) > mark:
            key, was = self.log.pop()
            if was is MISS:
                self.val.pop(key, None)
            else:
                self.val[key] = was
            self.moved.add(key)

    def forget(self, mark):
        del self.log[mark:]

    def drain(self):
        out = self.moved
        self.moved = set()
        return out


def satisfied(goal, val):
    got = val.get(goal.key, MISS)
    if goal.kind == "at":
        return got is not MISS and got == goal.val
    if goal.kind == "up":
        return got is not MISS and got >= goal.val
    return got is MISS


def episode(cfg, one, rec, out):
    goals = one.goals
    total = len(goals)
    by_key = {}
    under = {}
    for goal in goals:
        by_key.setdefault(goal.key, []).append(goal.gid)
        for up in goal.pre:
            under.setdefault(up, []).append(goal.gid)

    held = set()
    shut = set()
    at_obs = {}
    wake = set(goal.gid for goal in goals if not goal.pre)

    bar_key = {}
    for bar in one.bars:
        bar_key.setdefault(bar.key, []).append(bar)
    was_at = {key: rec.val.get(key, MISS) for key in bar_key}

    opened = rec.mark()
    rec.drain()
    spent = 0
    stopped = False
    now = 0

    for actions, good in one.steps:
        began = rec.mark()
        ran_out = False
        for op, key, value in actions:
            if spent >= cfg.budget:
                ran_out = True
                break
            if op == "put":
                rec.put(key, value)
            else:
                rec.cut(key)
            spent += 1
        if ran_out or not good:
            rec.back_to(began)
            if ran_out:
                stopped = True
                break
            continue

        now += 1
        moved = rec.drain()
        look = set(wake)
        wake = set()
        for key in moved:
            look.update(by_key.get(key, ()))

        val = rec.val
        fresh = []
        for gid in sorted(look):
            goal = goals[gid]
            if gid in shut:
                if not satisfied(goal, val):
                    shut.discard(gid)
                continue
            if gid in held:
                continue
            ready = True
            for up in goal.pre:
                if up not in held or at_obs[up] >= now:
                    ready = False
                    break
            if ready and satisfied(goal, val):
                held.add(gid)
                at_obs[gid] = now
                fresh.append(gid)
        for gid in fresh:
            out.line("mark %d" % gid)
            for down in under.get(gid, ()):
                wake.add(down)

        seen_bars = []
        for key in moved:
            seen_bars.extend(bar_key.get(key, ()))
        for bar in sorted(seen_bars, key=lambda one: one.bid):
            before = was_at.get(bar.key, MISS)
            after = val.get(bar.key, MISS)
            if bar.kind == "lost":
                hit = before is not MISS and after is MISS
            elif bar.kind == "gain":
                hit = before is MISS and after is not MISS
            else:
                hit = before is not MISS and after is not MISS and after < before
            if not hit:
                continue
            out.line("fire %d" % bar.bid)
            reach = {bar.goal}
            line = deque([bar.goal])
            while line:
                here = line.popleft()
                for down in under.get(here, ()):
                    if down not in reach:
                        reach.add(down)
                        line.append(down)
            for gid in sorted(reach):
                if gid in held:
                    held.discard(gid)
                    at_obs.pop(gid, None)
                    out.line("void %d" % gid)
                    for down in under.get(gid, ()):
                        wake.add(down)
            shut.add(bar.goal)
            wake.add(bar.goal)

        for key in moved:
            if key in was_at:
                was_at[key] = val.get(key, MISS)

    if stopped:
        rec.back_to(opened)
    rec.forget(opened)
    rec.drain()
    got = sum(goals[gid].weight for gid in held)
    whole = sum(goal.weight for goal in goals)
    out.line("ep %s %d %d %d" % (one.name, got, whole, spent))
    return got, whole, total


class Lines:
    __slots__ = ("lines",)

    def __init__(self):
        self.lines = []

    def line(self, text):
        self.lines.append(text)


def expect(program):
    """The lines a correct engine prints for this trail."""
    cfg, seeds, eps = spec.parse("\n".join(program) + "\n")
    rec = Rec()
    for key, value in seeds:
        rec.val[key] = value
    out = Lines()
    count = 0
    full = 0
    got_all = 0
    whole_all = 0
    for one in eps:
        got, whole, _n = episode(cfg, one, rec, out)
        count += 1
        got_all += got
        whole_all += whole
        if got == whole:
            full += 1
    out.line("run %d %d %d %d" % (count, full, got_all, whole_all))
    return out.lines
