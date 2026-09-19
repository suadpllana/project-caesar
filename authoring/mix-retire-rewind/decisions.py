"""The graded decisions as rows of integers the agent can read, for tools/onelinecheck.py.

Each row holds the candidates a solver would actually reach for at that moment - the naive
single-pattern count, the epoch a delivered count divides into, the record fields a resume
could be computed from - and the label is what the sealed model settles on. Where a short rule
reproduces the label, that decision is one a model writes cold; the task rests on the ones
where none does.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "mix-retire-rewind"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import gen  # noqa: E402
import model  # noqa: E402


def feed_for(lines):
    """A sealed feeder with the plan's corpus and mix applied, and nothing run yet."""
    feed = model.Feed()
    for line in lines:
        part = tuple(line.split())
        if part[0] in ("seed", "cap", "src", "mix"):
            feed.ex(part)
    return feed


def tally(pat, j, wide):
    whole, rest = divmod(wide, len(pat))
    return whole * pat.count(j) + pat[:rest].count(j)


def plans(per=6):
    out = []
    for fam, _name, lines in gen.programs("decisions", per):
        if fam in ("wide", "deep"):
            continue
        out.append(lines)
    return out


def samples():
    slot_source, took_at, retire_slot = [], [], []
    record_epoch, record_cursor, load_base, rank_of_offset = [], [], [], []

    for lines in plans():
        feed = feed_for(lines)
        opening = list(feed.pat)
        span = len(opening)
        for slot in range(0, 140, 7):
            j = feed.owner(slot)
            slot_source.append(({
                "slot": slot,
                "span": span,
                "naive_source": opening[slot % span],
                "live_span": len(feed.pats[feed.stretch(slot)]),
                "stretches": len(feed.starts),
            }, j))
            took = feed.delivered(slot)
            for who in sorted(set(opening)):
                naive = tally(opening, who, slot)
                row = {
                    "slot": slot,
                    "span": span,
                    "in_pattern": opening.count(who),
                    "naive_took": naive,
                    "fits": feed.fits(who),
                    "samples": len(feed.lens[who]),
                    "allowance": feed.hold[who],
                    "quota": feed.fits(who) * feed.hold[who],
                    "stretches": len(feed.starts),
                }
                took_at.append((dict(row), took[who]))
                if not feed.spent(who, took[who]) and took[who]:
                    ep, cur = feed.stands(who, took[who])
                    seen = {
                        "took": took[who],
                        "fits": feed.fits(who),
                        "samples": len(feed.lens[who]),
                        "by_fits": (took[who] - 1) // feed.fits(who),
                        "by_samples": (took[who] - 1) // len(feed.lens[who]),
                        "left_fits": (took[who] - 1) % feed.fits(who),
                        "left_samples": (took[who] - 1) % len(feed.lens[who]),
                    }
                    record_epoch.append((dict(seen), ep))
                    record_cursor.append((dict(seen), cur))

        for who in sorted(set(opening)):
            if not feed.hold[who]:
                continue
            feed.grow(4000)
            gone = None
            for i, pat in enumerate(feed.pats):
                if who not in pat:
                    gone = feed.starts[i] - 1
                    break
            if gone is None:
                continue
            quota = feed.fits(who) * feed.hold[who]
            per = opening.count(who)
            retire_slot.append(({
                "quota": quota,
                "fits": feed.fits(who),
                "allowance": feed.hold[who],
                "samples": len(feed.lens[who]),
                "in_pattern": per,
                "span": span,
                "naive_slot": (quota - 1) // per * span,
                "flat_slot": quota * span // per,
            }, gone))

        for base in (0, 17, 256):
            for done, made, wide in ((3, 7, 8), (5, 5, 4), (1, 9, 16), (12, 14, 2)):
                load_base.append(({
                    "base": base,
                    "done": done,
                    "made": made,
                    "wide": wide,
                    "done_span": done * wide,
                    "made_span": made * wide,
                    "from_done": base + done * wide,
                    "from_made": base + made * wide,
                }, base + done * wide))

        for world, micro, accum in ((2, 2, 2), (4, 1, 2), (1, 3, 1)):
            for o in range(world * micro * accum):
                rank_of_offset.append(({
                    "offset": o,
                    "world": world,
                    "micro": micro,
                    "accum": accum,
                    "by_turn": o % world,
                    "by_block": o // (micro * accum),
                    "seat": o // world,
                }, o % world))

    return {
        "slot_source": slot_source,
        "took_at_slot": took_at,
        "retire_slot": retire_slot,
        "record_epoch": record_epoch,
        "record_cursor": record_cursor,
        "load_base": load_base,
        "rank_of_offset": rank_of_offset,
    }
