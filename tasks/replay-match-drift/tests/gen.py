"""Run files generated inside the verifier, from a seed drawn after the agent has finished.

Each family is shaped around one decision, because an unshaped population does not exercise
a mechanism: the interleavings, the answer orders and the boundary positions here are placed
deliberately rather than sampled and hoped for.

  plain  the body matches its log exactly, one kind, answers in issue order - the ordinary
         case an engine that goes live on anything unfamiliar fails
  mix    three kinds whose recorded interleaving differs from the order the body issues
         them, so a command counted on the whole log lands on another kind's record
  swap   one kind, distinct names, answers recorded in an order that is not the issue order
  dup    the same kind and name issued several times beside distinct ones, so the answer
         counter has to be on the pair
  edge   a log that stops part way, so the run crosses to the live side and takes the
         values the run file offers
  left   a full log carrying recorded commands the body never issues
  late   both at once: the run crosses on one kind and still owes another kind's record
  sigs   several tags recorded out of the order they are waited for, some never taken
  vers   markers that decide which arm runs, recorded and not, on both sides of the boundary
  race   bursts of outstanding commands answered out of the order they were issued
  hold   a recorded command with no recorded answer
  bad    a recorded command under another name
  long   the scale family: a long log against a long body
  wide   the scale family: many races over a long log
"""
import random

FAMILIES = [
    ("plain", False), ("mix", False), ("swap", False), ("dup", False),
    ("edge", False), ("left", False), ("late", False), ("sigs", False),
    ("vers", False), ("race", False), ("hold", False), ("bad", False),
    ("long", True), ("wide", True),
]

KINDS = ("call", "child", "timer")
TAKE_OP = {"call": "call", "child": "spawn", "timer": "nap"}
OPEN_OP = {"call": "fire", "child": "open"}
NAMES = ("ax", "bo", "cy", "de", "ef", "gu", "ho", "ir", "ja", "ko", "lu", "mi")
TAGS = ("pay", "ship", "pack", "fix")
KEYS = ("road", "shape", "turn", "grip")


def _names(rng, n, unique):
    if unique:
        pool = list(NAMES)
        rng.shuffle(pool)
        while len(pool) < n:
            pool.append("%s%d" % (rng.choice(NAMES), len(pool)))
        return pool[:n]
    return [rng.choice(NAMES[:5]) for _ in range(n)]


def _merge(rng, cmds, drop, ok_order):
    """Interleave the recorded commands with their answers, answers never before their own."""
    events = []
    placed = set()
    gi = 0
    oi = 0
    order = [at for at in ok_order if at not in drop]
    while gi < len(cmds) or oi < len(order):
        ready = oi < len(order) and order[oi] in placed
        if gi < len(cmds) and (not ready or rng.random() < 0.55):
            kind, name, _v = cmds[gi]
            events.append("e go %s %s" % (kind, name))
            placed.add(gi)
            gi += 1
        elif ready:
            at = order[oi]
            kind, name, value = cmds[at]
            events.append("e ok %s %s %d" % (kind, name, value))
            oi += 1
        else:
            kind, name, _v = cmds[gi]
            events.append("e go %s %s" % (kind, name))
            placed.add(gi)
            gi += 1
    return events


def _sprinkle(rng, events, extra):
    """Place extra rows among the events, keeping the order they were given in."""
    spots = sorted(rng.randrange(len(events) + 1) for _ in extra)
    out = []
    at = 0
    for i in range(len(events) + 1):
        while at < len(spots) and spots[at] == i:
            out.append(extra[at])
            at += 1
        if i < len(events):
            out.append(events[i])
    return out


def _body_from(rng, cmds, bursts):
    """Body ops that issue cmds in order, some through outstanding bursts."""
    body = []
    at = 0
    n = len(cmds)
    while at < n:
        kind = cmds[at][0]
        room = 0
        while at + room < n and cmds[at + room][0] in OPEN_OP:
            room += 1
        if bursts and room >= 2 and rng.random() < 0.85:
            size = rng.randint(2, min(4, room))
            for k in range(size):
                body.append("b %s %s" % (OPEN_OP[cmds[at + k][0]], cmds[at + k][1]))
            for _ in range(size):
                body.append("b %s" % ("race" if rng.random() < 0.5 else "join"))
            at += size
            continue
        body.append("b %s %s" % (TAKE_OP[kind], cmds[at][1]))
        if rng.random() < 0.25:
            body.append("b add %d" % rng.randint(1, 5))
        at += 1
    return body


def _one(rng, fam):
    kinds = ("call",) if fam in ("plain", "swap", "dup", "hold") else KINDS
    if fam == "mix":
        kinds = KINDS
    size = {"long": 0, "wide": 0}.get(fam, rng.randint(4, 9))
    if fam == "long":
        return _long(rng)
    if fam == "wide":
        return _wide(rng)
    if fam == "vers":
        return _vers(rng)

    unique = fam in ("swap", "race", "left", "late", "edge", "bad")
    picked = _names(rng, size, unique)
    cmds = []
    for i in range(size):
        kind = rng.choice(kinds)
        cmds.append((kind, picked[i], rng.randint(0, 99)))
    if fam == "dup":
        for i in range(1, size):
            if rng.random() < 0.5:
                cmds[i] = (cmds[i - 1][0], cmds[i - 1][1], rng.randint(0, 99))

    live_from = size
    if fam == "edge":
        live_from = rng.randint(1, size - 1)
    if fam == "late":
        last = cmds[-1][0]
        cut = [i for i, c in enumerate(cmds) if c[0] == last]
        live_from = cut[max(0, len(cut) - rng.randint(1, 2))]
    recorded = cmds[:live_from]

    drop = set()
    if fam == "hold" and recorded:
        drop.add(rng.randrange(len(recorded)))

    ok_order = list(range(len(recorded)))
    if fam == "race":
        ok_order.reverse()
    elif fam in ("swap", "dup", "mix"):
        rng.shuffle(ok_order)

    body = _body_from(rng, cmds, fam in ("race", "mix", "left", "late", "edge"))
    rows = []
    if fam == "sigs":
        tags = list(TAGS[:rng.randint(2, 4)])
        rows = ["e sig %s %d" % (rng.choice(tags), rng.randint(10, 99))
                for _ in range(rng.randint(4, 8))]
        body = _with_waits(rng, body, rows, rng.random() < 0.25)
    body.append("b fin")

    events = _merge(rng, recorded, drop, ok_order)
    if fam == "mix":
        events = _shuffle_go(rng, events)
    if fam in ("left", "late"):
        other = [k for k in KINDS if k != cmds[-1][0]] if fam == "late" else list(KINDS)
        spare = ["e go %s %s" % (rng.choice(other), rng.choice(NAMES))
                 for _ in range(rng.randint(1, 2))]
        events = events + spare
    if fam == "sigs":
        events = _sprinkle(rng, events, rows)
    if fam == "bad" and events:
        events = _rename(rng, events)

    spare = max(0, size - live_from) + 2
    feed = ["r %d" % rng.randint(1, 99) for _ in range(spare)]
    return body + events + feed


def _shuffle_go(rng, events):
    """Move the recorded commands around without changing their order inside a kind."""
    slots = [i for i, row in enumerate(events) if row.startswith("e go ")]
    rows = [events[i] for i in slots]
    by_kind = {}
    for row in rows:
        by_kind.setdefault(row.split()[2], []).append(row)
    order = []
    while any(by_kind.values()):
        live = [k for k in by_kind if by_kind[k]]
        pick = rng.choice(live)
        order.append(by_kind[pick].pop(0))
    out = list(events)
    for i, row in zip(slots, order):
        out[i] = row
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


def _with_waits(rng, body, rows, overdraw):
    """Waits drawn from the signals that were actually recorded, so most of them land."""
    have = {}
    for row in rows:
        have[row.split()[2]] = have.get(row.split()[2], 0) + 1
    want = []
    for tag, n in sorted(have.items()):
        want.extend([tag] * (n if overdraw else max(1, n - rng.randint(0, 1))))
    if overdraw:
        want.append(sorted(have)[0])
    rng.shuffle(want)
    out = []
    for row in body:
        out.append(row)
        if want and rng.random() < 0.45:
            out.append("b wait %s" % want.pop())
    out.extend("b wait %s" % tag for tag in want)
    return out


def _vers(rng):
    """Markers that choose an arm, with the arm the generator knows is taken."""
    body = []
    cmds = []
    events = []
    chs = []
    kept = rng.randint(3, 5)
    rec_cmds = rng.randint(1, kept - 1) if rng.random() < 0.6 else kept
    for step in range(kept):
        key = KEYS[step % 2]
        cur = rng.randint(1, 3)
        if rng.random() < 0.45:
            value = rng.choice([0, cur])
            chs.append("e ch %s %d" % (key, value))
        else:
            value = cur if len(cmds) >= rec_cmds + 1 else 0
        body.append("b mark %s %d" % (key, cur))
        body.append("b jz arm%d" % step)
        hot = (rng.choice(KINDS), rng.choice(NAMES), rng.randint(0, 99))
        cold = (rng.choice(KINDS), rng.choice(NAMES), rng.randint(0, 99))
        body.append("b %s %s" % (TAKE_OP[hot[0]], hot[1]))
        body.append("b jmp out%d" % step)
        body.append("b lab arm%d" % step)
        body.append("b %s %s" % (TAKE_OP[cold[0]], cold[1]))
        body.append("b lab out%d" % step)
        cmds.append(cold if value == 0 else hot)
    body.append("b fin")
    events = _merge(rng, cmds[:rec_cmds], set(), list(range(rec_cmds)))
    events = _sprinkle(rng, events, chs)
    feed = ["r %d" % rng.randint(1, 99) for _ in range(kept + 2)]
    return body + events + feed


def _long(rng):
    size = 30000
    picked = ["n%d" % (i % 700) for i in range(size)]
    cmds = [(KINDS[i % 3], picked[i], (i * 7) % 100) for i in range(size)]
    body = [("b %s %s" % (TAKE_OP[c[0]], c[1])) for c in cmds]
    body.append("b fin")
    events = []
    for kind, name, value in cmds:
        events.append("e go %s %s" % (kind, name))
        events.append("e ok %s %s %d" % (kind, name, value))
    return body + events


def _wide(rng):
    size = 22000
    cmds = [("call" if i % 2 else "child", "w%d" % i, (i * 11) % 100) for i in range(size)]
    body = []
    at = 0
    while at < size:
        room = min(4, size - at)
        for k in range(room):
            body.append("b %s %s" % (OPEN_OP[cmds[at + k][0]], cmds[at + k][1]))
        for _ in range(room):
            body.append("b race")
        at += room
    body.append("b fin")
    gos = ["e go %s %s" % (c[0], c[1]) for c in cmds]
    oks = ["e ok %s %s %d" % (c[0], c[1], c[2]) for c in cmds]
    events = []
    for at in range(0, size, 4):
        events.extend(gos[at:at + 4])
        block = oks[at:at + 4]
        block.reverse()
        events.extend(block)
    return body + events


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        count = 3 if big else per
        for i in range(count):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append((fam, "%s-%d" % (fam, i), _one(rng, fam)))
    return out
