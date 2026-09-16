"""Plan generator for the graded families.

Each family is shaped around one mechanism of the contract so that a wrong
reading of that mechanism moves lines in a measurable fraction of the family,
rather than in a handful of lucky plans:

  plain  no shifts and little contention - the C1 fence, ordinary runs only
  shift  every zone moves at least once, anchors aimed at the moved hour
  press  long runs and overlapping windows, so runs wait for the lane
  cap    pool caps of one or two, so runs wait for the day to roll over
  mix    a pool whose zone differs from its jobs', so the local dates disagree
  drift  follow jobs whose step does not divide the day, so they leave the
         window, drop, and re-enter on the attempt chain

`plans(nonce, per)` is what the verifier calls; the nonce makes the graded
population unavailable before the run.
"""

import hashlib
import random

FAMILIES = ("plain", "shift", "press", "cap", "mix", "drift")

ZONE_NAMES = ("coast", "inland", "island", "ridge")
POOL_NAMES = ("main", "side", "aux")
JOB_NAMES = ("sweep", "purge", "rollup", "tally", "flush", "scan", "verify")


def seed_for(nonce, family, i):
    h = hashlib.sha256(("%s|%s|%d" % (nonce, family, i)).encode()).hexdigest()
    return int(h[:16], 16)


def make_zones(rng, family, count):
    out = []
    for i in range(count):
        name = ZONE_NAMES[i]
        base = rng.choice([-180, -120, -60, 0, 30, 60, 120]) if i else rng.choice([0, 60])
        shifts = []
        want = 2 if family == "shift" else rng.choice([0, 0, 1, 2])
        if family == "mix" and not want:
            want = 1
        at = rng.randrange(600, 1500)
        off = base
        for _ in range(want):
            off = off + rng.choice([-60, 60])
            shifts.append((at, off))
            at += rng.randrange(1000, 2600)
        out.append((name, base, shifts))
    return out


def window_for(rng, family):
    opn = rng.randrange(0, 20) * 60
    span = rng.choice([120, 180, 240, 300, 360, 480])
    shut = min(opn + span, 1440)
    if shut - opn < 60:
        opn, shut = 0, 360
    return opn, shut


def make_job(rng, family, name, prio, zones, pools):
    zone = rng.choice(zones)
    zname = zone[0]
    pname = rng.choice(pools)[0]
    opn, shut = window_for(rng, family)
    if family == "press":
        dur = rng.choice([120, 180, 240, 300])
    elif family == "plain":
        dur = rng.choice([20, 30, 45, 60])
    else:
        dur = rng.choice([30, 45, 60, 90, 120])
    if family == "drift":
        mode = "clock" if rng.random() < 0.3 else "follow"
    elif family == "plain":
        mode = "clock" if rng.random() < 0.7 else "follow"
    else:
        mode = rng.choice(["clock", "follow"])
    if mode == "follow":
        step = dur + rng.choice([30, 60, 150, 210, 250, 290, 370, 430])
        if family == "drift":
            step = dur + rng.choice([150, 210, 250, 290, 370])
    else:
        step = rng.choice([180, 240, 360, 480, 720, 1440, 1440, 1440])
        if family == "press":
            step = rng.choice([240, 360, 480, 720])
    anchor = opn + rng.randrange(0, max(1, shut - opn))
    if family == "shift":
        anchor = opn + rng.randrange(0, max(1, min(240, shut - opn)))
    # The first occurrence must not fall before the plan's epoch, which is what the
    # shipped validator enforces; push the anchor forward by whole local days so its
    # time of day is untouched.
    top = max([zone[1]] + [o for _, o in zone[2]])
    while anchor < top:
        anchor += 1440
    return "job %s %s %d %s %d %d %d %s %d %d" % (
        name, zname, prio, pname, dur, opn, shut, mode, step, anchor)


def one(nonce, family, i):
    rng = random.Random(seed_for(nonce, family, i))
    zcount = 1 if family == "plain" and rng.random() < 0.5 else rng.choice([2, 2, 3])
    zones = make_zones(rng, family, zcount)
    pcount = 1 if family == "cap" else rng.choice([1, 2])
    pools = []
    for pi in range(pcount):
        pz = zones[(pi + 1) % len(zones)][0] if family == "mix" else rng.choice(zones)[0]
        if family == "cap":
            cap = rng.choice([1, 2])
        elif family == "plain":
            cap = rng.choice([6, 8])
        else:
            cap = rng.choice([2, 3, 4])
        pools.append((POOL_NAMES[pi], pz, cap))
    jcount = rng.choice([2, 3]) if family == "plain" else rng.choice([3, 4, 5])
    lines = []
    for name, base, shifts in zones:
        lines.append("zone %s %d" % (name, base))
        for at, off in shifts:
            lines.append("shift %s %d %d" % (name, at, off))
    for pname, pz, cap in pools:
        lines.append("pool %s %s %d" % (pname, pz, cap))
    order = list(range(1, jcount + 1))
    rng.shuffle(order)
    for n in range(jcount):
        lines.append(make_job(rng, family, JOB_NAMES[n], order[n], zones, pools))
    horizon = rng.choice([2880, 4320, 4320, 5760])
    lines.append("horizon %d" % horizon)
    return "\n".join(lines) + "\n"


def plans(nonce, per):
    out = []
    for family in FAMILIES:
        for i in range(per):
            out.append(("%s-%03d" % (family, i), one(nonce, family, i)))
    return out
