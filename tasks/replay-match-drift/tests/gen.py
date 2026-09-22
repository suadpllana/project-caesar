"""Run files generated inside the verifier, from a seed drawn after the agent has finished.

A history is a recording, so these are produced by simulating one: the generator forks the
branches, issues each branch's commands in the order the scheduling rules put them, and
gives every answer a key that decides where its line lands. Sorting by those keys at the end
turns the simulation into a history the engine reproduces, which is why the recorded
interleavings here are the ones a real run would leave rather than a shuffle.

Each family is shaped around one decision, because an unshaped population does not exercise
a mechanism.

  plain  one branch, answers recorded in the order the work was issued - the ordinary case
  mix    one branch over three kinds, whose recorded interleaving is not the issue order
  swap   one branch whose answers were recorded in the opposite order
  dup    the same kind and name issued several times, and one name used under two kinds
  pair   two branches whose answers interleave, so the schedule alternates between them
  many   four to seven branches whose marks reorder the run away from fork order
  sigs   several tags, with two branches competing for the same one
  vers   markers deciding which arm a branch takes, recorded and not, on both sides
  edge   a history that stops part way, so the run comes to a standstill and goes live
  left   a full history carrying recorded commands the body never issues
  late   both at once: the run goes live and still owes the history a command
  stop   branch zero ending while other branches are still waiting
  bad    a recorded command under another name
  long   the scale family for the history tables: one branch, a long history
  wide   the scale family for the schedule: eight thousand branches over a long history
"""
import heapq
import random

FAMILIES = [
    ("plain", False), ("mix", False), ("swap", False), ("dup", False),
    ("pair", False), ("many", False), ("sigs", False), ("vers", False),
    ("edge", False), ("left", False), ("late", False), ("stop", False),
    ("bad", False), ("long", True), ("wide", True),
]

KINDS = ("call", "child", "timer")
AWAIT_OP = {"call": "call", "child": "spawn", "timer": "nap"}
NAMES = ("ax", "bo", "cy", "de", "ef", "gu", "ho", "ir", "ja", "ko", "lu", "mi")
TAGS = ("pay", "ship", "pack", "fix")
KEYS = ("road", "shape")


class Step(object):
    """One thing a branch does, in the order it does it."""

    def __init__(self, what, kind=None, name=None, tag=None, key=None, cur=0):
        self.what = what
        self.kind = kind
        self.name = name
        self.tag = tag
        self.key = key
        self.cur = cur


def _names(rng, n, unique):
    if unique:
        pool = list(NAMES)
        rng.shuffle(pool)
        while len(pool) < n:
            pool.append("%s%d" % (rng.choice(NAMES), len(pool)))
        return pool[:n]
    return [rng.choice(NAMES[:4]) for _ in range(n)]


def _body(plans, labels):
    """Branch zero forks every other block, then runs its own steps."""
    rows = []
    for at in range(1, len(plans)):
        rows.append("b fork %s" % labels[at])
    rows.extend(_steps(plans[0]))
    rows.append("b end")
    for at in range(1, len(plans)):
        rows.append("b lab %s" % labels[at])
        rows.extend(_steps(plans[at]))
        rows.append("b end")
    return rows


def _steps(plan):
    rows = []
    for step in plan:
        if step.what == "await":
            rows.append("b %s %s" % (AWAIT_OP[step.kind], step.name))
        elif step.what == "fire":
            rows.append("b fire %s" % step.name)
        elif step.what == "take":
            rows.append("b take")
        elif step.what == "wait":
            rows.append("b wait %s" % step.tag)
        elif step.what == "mark":
            rows.append("b mark %s %d" % (step.key, step.cur))
        elif step.what == "add":
            rows.append("b add %d" % step.cur)
    return rows


def _sim(rng, plans, delay):
    """Walk the branches the way the scheduling rules do, recording as we go.

    Every event gets a sort key. A command's own line takes the clock it was issued at; its
    answer takes that clock plus a delay, which is what decides how far down the history the
    branch's next turn lands. Sorting by key gives a history whose positions reproduce the
    simulated schedule, so the recorded interleaving is one a real run would have left.
    """
    events = []
    clock = [0.0]
    # Keys have to be distinct: two answers landing on one key would be ordered by the sort
    # here and by their line position in the engine, and the two orders need not agree.
    nudge = [0]
    at = [0] * len(plans)
    held = [[] for _ in plans]
    ready = list(range(len(plans)))
    waiting = []
    sig_key = {}

    def tick():
        clock[0] += 1.0
        return clock[0]

    def apart(key):
        nudge[0] += 1
        return key + nudge[0] * 1e-7

    while ready or waiting:
        if ready:
            bid = ready.pop(0)
        else:
            bid = heapq.heappop(waiting)[1]
        plan = plans[bid]
        while at[bid] < len(plan):
            step = plan[at[bid]]
            at[bid] += 1
            if step.what in ("await", "fire"):
                key = tick()
                events.append((key, "e go %s %s" % (step.kind, step.name)))
                done = apart(key + delay(rng, bid, at[bid]))
                if step.what == "fire":
                    held[bid].append((step, done))
                    continue
                events.append((done, "e ok %s %s %d"
                               % (step.kind, step.name, rng.randint(0, 99))))
                heapq.heappush(waiting, (done, bid))
                break
            if step.what == "take":
                if not held[bid]:
                    continue
                step_held, done = held[bid].pop(0)
                events.append((done, "e ok %s %s %d"
                               % (step_held.kind, step_held.name, rng.randint(0, 99))))
                heapq.heappush(waiting, (done, bid))
                break
            if step.what == "wait":
                key = apart(max(sig_key.get(step.tag, 0.0) + 0.25, tick()))
                sig_key[step.tag] = key
                events.append((key, "e sig %s %d" % (step.tag, rng.randint(10, 99))))
                heapq.heappush(waiting, (key, bid))
                break
    events.sort(key=lambda row: row[0])
    return [row[1] for row in events]


def _plans(rng, fam):
    """The branches and what each of them does."""
    count = {"plain": 1, "mix": 1, "swap": 1, "dup": 1, "bad": 1, "left": 1,
             "pair": 2, "stop": 3}.get(fam, rng.randint(2, 5))
    if fam == "many":
        count = rng.randint(4, 7)
    kinds = ("call",) if fam in ("plain", "swap", "dup") else KINDS
    if fam == "late":
        kinds = KINDS[:2]
    each = rng.randint(2, 4)
    longest = each + 2 * (count - 1) if fam != "stop" else each
    unique = fam not in ("dup",)
    pool = _names(rng, count * each + 4, unique)
    take = 0
    plans = []
    for bid in range(count):
        plan = []
        for _i in range(longest if bid == 0 else each):
            name = pool[take % len(pool)]
            take += 1
            kind = rng.choice(kinds)
            if fam in ("pair", "many", "stop", "edge", "late") and rng.random() < 0.3:
                plan.append(Step("fire", kind="call", name=name))
                plan.append(Step("take"))
            else:
                plan.append(Step("await", kind=kind, name=name))
            if rng.random() < 0.3:
                plan.append(Step("add", cur=rng.randint(1, 5)))
        plans.append(plan)
    if fam == "sigs":
        tags = list(TAGS[:rng.randint(2, 3)])
        for plan in plans:
            plan.insert(rng.randrange(len(plan) + 1), Step("wait", tag=rng.choice(tags)))
        plans[0].insert(0, Step("wait", tag=tags[0]))
        if len(plans) > 1:
            plans[1].insert(0, Step("wait", tag=tags[0]))
    if fam == "vers":
        for plan in plans:
            plan.insert(0, Step("mark", key=rng.choice(KEYS), cur=rng.randint(1, 3)))
    return plans


def _one(rng, fam):
    if fam == "long":
        return _long(rng)
    if fam == "wide":
        return _wide(rng)

    plans = _plans(rng, fam)
    labels = ["main"] + ["arm%d" % at for at in range(1, len(plans))]
    pool = {"swap": (7.5, 6.5, 5.5), "mix": (0.5, 3.5, 6.5), "dup": (0.5, 4.5),
            "pair": (0.5, 2.5), "many": (0.5, 1.5, 3.5, 7.5)}.get(fam, (0.5, 1.5, 2.5))
    body = _body(plans, labels)
    events = _sim(rng, plans, lambda r, b, i: r.choice(pool))

    if fam == "vers":
        keys = sorted({step.key for plan in plans for step in plan if step.what == "mark"})
        rows = ["e ch %s %d" % (key, rng.choice([0, rng.randint(1, 3)]))
                for key in keys if rng.random() < 0.6]
        events = _place(rng, events, rows)

    if fam in ("edge", "late", "stop"):
        cut = rng.randint(max(1, len(events) // 3), max(2, len(events) - 2))
        events = events[:cut]
    if fam in ("left", "late"):
        spare = KINDS[2] if fam == "late" else rng.choice(KINDS)
        events = events + ["e go %s %s" % (spare, rng.choice(NAMES))
                           for _ in range(rng.randint(1, 2))]
    if fam == "bad":
        events = _rename(rng, events)

    feed = ["r %d" % rng.randint(1, 99) for _ in range(len(body) // 2 + 3)]
    return body + events + feed


def _place(rng, events, rows):
    spots = sorted(rng.randrange(len(events) + 1) for _ in rows)
    out = []
    at = 0
    for i in range(len(events) + 1):
        while at < len(spots) and spots[at] == i:
            out.append(rows[at])
            at += 1
        if i < len(events):
            out.append(events[i])
    return out


def _rename(rng, events):
    slots = [i for i, row in enumerate(events) if row.startswith("e go ")]
    if not slots:
        return events
    at = rng.choice(slots[len(slots) // 2:])
    part = events[at].split()
    out = list(events)
    out[at] = "e go %s %s" % (part[2], part[3] + "z")
    return out


def _long(rng):
    """One branch, a long history: the gate on the tables the history is read through."""
    size = 24000
    plan = [Step("await", kind=KINDS[i % 3], name="n%d" % (i % 600)) for i in range(size)]
    body = _body([plan], ["main"])
    events = _sim(rng, [plan], lambda r, b, i: 0.5)
    return body + events


def _wide(rng):
    """Three thousand branches whose answers are scattered, so the queue never empties."""
    arms = 8000
    each = 8
    plans = []
    for at in range(arms):
        plans.append([Step("await", kind="call", name="w%d-%d" % (at, step))
                      for step in range(each)])
    labels = ["main"] + ["a%d" % at for at in range(1, arms)]
    body = _body(plans, labels)
    # branch zero waits longest at every step, so it is the last to finish and the run ends
    # on its own value rather than on what the others left behind
    events = _sim(rng, plans, lambda r, b, i:
                  40000.0 + i * 500.0 if b == 0 else r.uniform(1.0, 36000.0))
    return body + events


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        count = 3 if big else per
        for i in range(count):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append((fam, "%s-%d" % (fam, i), _one(rng, fam)))
    return out
