#!/usr/bin/env python3
"""Build environment/app_src/tok/merges.json.

The merge table is the data the whole task turns on, so it is generated rather than
hand-written, and the properties the design depends on are asserted here instead of
being hoped for.

A byte-pair table is trained over a synthetic corpus of the kind of text this loop
carries - short operator questions and tool output lines - and then filtered so that the
positions an encode may safely be resumed from are exactly the ones the design wants.

A boundary between two characters survives every encode of every surrounding text when
nothing can reach across it, and there are two ways for that to be true: the character
after it never sits anywhere but at the front of a symbol, or the character before it
never sits anywhere but at the end of one. Neither condition implies the other, and both
sets are non-empty here, which is asserted below. A solver that finds only the first
condition is safe and pays for it in characters.

Two of the front-only characters (# and @) do appear as the left half of merges, so the
cruder question - which characters take part in no merge at all - gives a strictly
smaller set again, and a third resume rule that is safe and more expensive still.

The marker that opens a reply is deliberately made to reach rightwards, so the boundary
in front of a reply is decided by the reply's own first character instead of being free
for everyone.

Usage:  python3 authoring/mktok.py
"""

from __future__ import annotations

import collections
import json
import random
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent

MARK = "\x01\x02\x03\x04"
BASE = MARK + "\n" + " " + "abcdefghijklmnopqrstuvwxyz" + "0123456789" + ".,:-/_=#@[]~"

# Characters that must never appear anywhere but at the front of a symbol.
FRONT = "\x01#@~]"
# Of those, the two that must also take part in merges, so that "appears in no merge"
# is a strictly weaker test than the one that matters.
FRONT_IN_MERGE = "#@"
# Characters that must be reachable from both directions, however special they look.
SOFT = "\x03\x04 "
# The marker that opens a reply has to reach rightwards, so that the boundary in front
# of a reply depends on what the reply starts with.
REACHES_RIGHT = "\x02"

N_MERGES = 256

VERBS = ["check", "list", "show", "trace", "count", "drain", "replay", "flush",
         "resume", "inspect", "compare", "reset", "audit", "widen", "pin"]
NOUNS = ["queue", "shard", "batch", "window", "lease", "worker", "buffer", "stream",
         "record", "offset", "cursor", "digest", "segment", "quota", "handle"]
ADJS = ["stale", "warm", "idle", "paused", "partial", "late", "wide", "narrow",
        "pinned", "dropped", "merged", "split"]
KEYS = ["status", "items", "lag", "depth", "retries", "age", "rate", "loss",
        "held", "sent", "acked", "gap"]
VALS = ["ok", "warn", "late", "drained", "held", "empty", "full", "mixed"]
SVC = ["ingest", "router", "planner", "shipper", "reducer", "walker", "keeper"]


def corpus(rng: random.Random) -> str:
    """Text of the shape this loop actually carries, in the four block markers."""
    out = []
    for _ in range(700):
        q = "%s the %s %s for #q%d" % (rng.choice(VERBS), rng.choice(ADJS),
                                       rng.choice(NOUNS), rng.randrange(1000, 9999))
        out.append("\x01" + q + "\x04")
        if rng.random() < 0.5:
            a = "sent %s %s, %s %s" % (rng.choice(NOUNS), rng.choice(ADJS),
                                       rng.choice(VERBS), rng.choice(NOUNS))
        else:
            a = "%s %s %s, %s %s" % (rng.choice(VERBS), rng.choice(NOUNS),
                                     rng.choice(ADJS), rng.choice(VERBS),
                                     rng.choice(NOUNS))
        out.append("\x02" + a + "\x04")
        t = "%s=%s %s=%d @w/%s/%s\n%s=%d" % (
            rng.choice(KEYS), rng.choice(VALS), rng.choice(KEYS),
            rng.randrange(0, 400), rng.choice(SVC), rng.choice(NOUNS),
            rng.choice(KEYS), rng.randrange(0, 90))
        out.append("\x03" + t + "\x04")
    return "".join(out)


def keep(pair: tuple[str, str]) -> bool:
    """Drop any merge that would put a front-only character out of first place."""
    return not any(c in FRONT for c in (pair[0] + pair[1])[1:])


def train(text: str, limit: int) -> list[tuple[str, str]]:
    """Ordinary byte-pair training: repeatedly merge the most frequent adjacent pair.

    The filter is applied while training rather than afterwards. Filtering after the fact
    does not work: the first pair the corpus offers is space followed by the handle
    marker, and once that merge exists every later symbol built on it carries the marker
    in a non-initial position and has to be thrown away, which takes the marker out of
    the table altogether.
    """
    merges: list[tuple[str, str]] = []
    seq = list(text)
    while len(merges) < limit:
        freq: dict[tuple[str, str], int] = collections.Counter()
        for i in range(len(seq) - 1):
            pair = (seq[i], seq[i + 1])
            if keep(pair):
                freq[pair] += 1
        if not freq:
            break
        best = max(sorted(freq), key=lambda p: freq[p])
        if freq[best] < 12:
            break
        merges.append(best)
        joined = best[0] + best[1]
        out = []
        i = 0
        while i < len(seq):
            if i + 1 < len(seq) and seq[i] == best[0] and seq[i + 1] == best[1]:
                out.append(joined)
                i += 2
            else:
                out.append(seq[i])
                i += 1
        seq = out
    return merges


def interior(merges: list[tuple[str, str]]) -> set[str]:
    """Characters that occur somewhere other than the front of a merged symbol."""
    seen: set[str] = set()
    for a, b in merges:
        seen.update((a + b)[1:])
    return seen


def carried(merges: list[tuple[str, str]]) -> set[str]:
    """Characters that occur somewhere other than the end of a merged symbol."""
    seen: set[str] = set()
    for a, b in merges:
        seen.update((a + b)[:-1])
    return seen


def in_any_merge(merges: list[tuple[str, str]]) -> set[str]:
    seen: set[str] = set()
    for a, b in merges:
        seen.update(a + b)
    return seen


def main() -> int:
    rng = random.Random(20260811)
    text = corpus(rng)
    for c in set(text):
        if c not in BASE:
            raise SystemExit("corpus uses a character outside the base set: %r" % c)

    merges = train(text, N_MERGES)

    inner = interior(merges)
    mid = carried(merges)
    used = in_any_merge(merges)

    front = sorted(c for c in BASE if c not in inner)
    back = sorted(c for c in BASE if c not in mid)
    weak = sorted(c for c in BASE if c not in used)

    for c in FRONT:
        if c in inner:
            raise SystemExit("front-only character %r ended up inside a merged symbol" % c)
    for c in FRONT_IN_MERGE:
        if c not in used:
            raise SystemExit("character %r takes part in no merge, so the cruder test "
                             "would find it too" % c)
    for c in SOFT:
        if c not in inner:
            raise SystemExit("character %r has to be reachable from the left, so that "
                             "cutting in front of it is unsafe" % c)
    for c in REACHES_RIGHT:
        if c not in mid:
            raise SystemExit("character %r never reaches rightwards, so the boundary "
                             "after it would be free" % c)
    if not set(front) - set(back) or not set(back) - set(front):
        raise SystemExit("one of the two conditions is subsumed by the other")
    if len(merges) < N_MERGES:
        raise SystemExit("only %d merges survived the filter" % len(merges))

    data = {"base": BASE, "merges": [list(p) for p in merges]}
    dst = TASK / "environment" / "app_src" / "tok" / "merges.json"
    dst.write_text(json.dumps(data, indent=0, ensure_ascii=False) + "\n")

    both = sorted(set(front) | set(back))
    print("merges           %d" % len(merges))
    print("symbols          %d" % (len(BASE) + len(merges)))
    print("never interior   %r" % "".join(front))
    print("never carried    %r" % "".join(back))
    print("resume points    %r" % "".join(both))
    print("in no merge      %r" % "".join(weak))
    print("missed by one    %r" % "".join(sorted(set(both) - set(front))))
    print("missed by crude  %r" % "".join(sorted(set(both) - set(weak))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
