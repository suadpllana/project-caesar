"""Short named sessions, and generated ones drawn from a per-run seed.

Each case is a whole session: a rail count, the state the part powers on in,
and a few batches. What is checked is where the part ends up after each batch
and whether it ever faulted. The transaction ceiling is not applied to these —
they are the correctness floor, and the ceiling belongs to the long sessions.

Both directions are covered on purpose: cases that need a rail taken down or
brought up, and cases that need a rail left exactly where it is. The second
group fails an apply path that takes rails down for the sake of it, and the
first fails one that has decided the enables are somebody else's problem.

The next group is about neighbours. A frame is cheaper than the writes it
replaces but it lands on every register it spans, so these put wanted rails
next to each other, put gaps between them, and park a rail under its own limit
right beside a rail that has to move.

The last two groups are about the pair register. Rails whose trim moves in one
half only, rails whose trim moves in both, a whole part in one frame, and the
rails no single word can describe: the ones the rack leaves sitting under their
own limit, which cannot ride inside a frame that spans them either.
"""

import random

import sessions

V, I, E = 0, 1, 2
POWER_ON = (50, 90, True)


def _start(rails):
    return ([POWER_ON[0]] * rails, [POWER_ON[1]] * rails, [POWER_ON[2]] * rails)


def _end(start, batches):
    """Where a correct apply path leaves the part after each batch."""
    v, i, e = [list(x) for x in start]
    out = []
    for reqs in batches:
        for kind, rail, value in reqs:
            if kind == V:
                v[rail] = value
            elif kind == I:
                i[rail] = value
            else:
                e[rail] = bool(value & 1)
        out.append((list(v), list(i), [bool(x) for x in e]))
    return out


def _case(name, rails, batches):
    start = _start(rails)
    return {
        "id": name,
        "rails": rails,
        "start": start,
        "session": list(zip(batches, _end(start, batches))),
    }


def named_cases():
    s = []

    # ---- a rail moving, and the part not objecting ------------------------
    s.append(_case("trim-one-rail-upward", 4, [
        [(I, 0, 95), (V, 0, 80)],
    ]))
    s.append(_case("walk-one-rail-downward", 4, [
        [(E, 1, 0), (V, 1, 20), (I, 1, 25), (E, 1, 1)],
    ]))
    s.append(_case("walk-a-rail-down-without-being-asked-to", 4, [
        [(V, 2, 18), (I, 2, 22)],
    ]))
    s.append(_case("raise-past-the-old-limit", 4, [
        [(I, 3, 99), (V, 3, 97)],
    ]))
    s.append(_case("limit-and-voltage-both-down-hard", 6, [
        [(E, 4, 0), (V, 4, 11), (I, 4, 12), (E, 4, 1)],
    ]))

    # ---- enables that have to happen --------------------------------------
    s.append(_case("rail-the-batch-leaves-down", 4, [
        [(E, 2, 0)],
    ]))
    s.append(_case("down-rail-retrimmed-then-brought-up", 4, [
        [(E, 1, 0)],
        [(V, 1, 30), (I, 1, 40), (E, 1, 1)],
    ]))
    s.append(_case("rail-left-down-and-retrimmed", 4, [
        [(E, 3, 0), (I, 3, 20), (V, 3, 15)],
    ]))
    s.append(_case("every-rail-down-then-every-rail-up", 3, [
        [(E, 0, 0), (E, 1, 0), (E, 2, 0)],
        [(E, 0, 1), (E, 1, 1), (E, 2, 1)],
    ]))
    s.append(_case("down-and-up-inside-one-batch", 4, [
        [(E, 0, 0), (V, 0, 25), (I, 0, 30), (E, 0, 1)],
    ]))

    # ---- enables that must not happen -------------------------------------
    s.append(_case("neighbours-are-left-alone", 6, [
        [(I, 2, 70), (V, 2, 60)],
    ]))
    s.append(_case("restating-what-is-already-in-force", 4, [
        [(V, 0, 50), (I, 0, 90), (E, 0, 1)],
    ]))
    s.append(_case("restating-across-two-batches", 4, [
        [(I, 1, 60), (V, 1, 55)],
        [(I, 1, 60), (V, 1, 55), (E, 1, 1)],
    ]))
    s.append(_case("an-empty-batch", 4, [
        [],
    ]))
    s.append(_case("a-batch-that-only-restates", 4, [
        [(V, 3, 50), (I, 3, 90), (E, 3, 1), (V, 3, 50)],
    ]))

    # ---- the batch's last word --------------------------------------------
    s.append(_case("last-word-on-a-register-wins", 4, [
        [(V, 0, 20), (V, 0, 30), (V, 0, 25)],
    ]))
    s.append(_case("enable-then-disable-ends-down", 4, [
        [(E, 2, 0), (E, 2, 1), (E, 2, 0)],
    ]))
    s.append(_case("disable-then-enable-ends-up", 4, [
        [(E, 2, 0), (E, 2, 1)],
    ]))
    s.append(_case("a-rail-mentioned-in-every-bank", 4, [
        [(E, 1, 0), (I, 1, 44), (V, 1, 40), (E, 1, 1), (V, 1, 35)],
    ]))

    # ---- several rails and several batches --------------------------------
    s.append(_case("four-rails-a-rail-at-a-time", 4, [
        [(I, 0, 95), (V, 0, 92), (E, 1, 0), (V, 2, 28), (I, 2, 30), (E, 3, 0)],
    ]))
    s.append(_case("state-carries-between-batches", 4, [
        [(I, 0, 95), (V, 0, 92)],
        [(V, 0, 20), (I, 0, 25)],
        [(E, 0, 0)],
    ]))
    s.append(_case("the-top-rail-of-the-part", 8, [
        [(V, 7, 30), (I, 7, 35)],
    ]))
    s.append(_case("one-rail-part", 1, [
        [(E, 0, 0), (V, 0, 12), (I, 0, 20), (E, 0, 1)],
    ]))
    s.append(_case("nothing-at-all-then-something", 4, [
        [],
        [(I, 1, 70), (V, 1, 65)],
    ]))
    s.append(_case("all-rails-walked-down-together", 5, [
        [(E, r, 0) for r in range(5)] +
        [(V, r, 20 + r) for r in range(5)] +
        [(I, r, 30 + r) for r in range(5)] +
        [(E, r, 1) for r in range(5)],
    ]))

    # ---- rails held under their own limit ---------------------------------
    s.append(_case("a-rail-parked-under-its-limit", 4, [
        [(E, 2, 0), (I, 2, 20)],
    ]))
    s.append(_case("a-parked-rail-brought-back-up", 4, [
        [(E, 1, 0), (I, 1, 15)],
        [(I, 1, 80), (V, 1, 45), (E, 1, 1)],
    ]))
    s.append(_case("a-parked-rail-beside-three-that-move", 5, [
        [(E, 3, 0), (I, 3, 18)],
        [(I, 0, 95), (V, 0, 92), (I, 1, 95), (V, 1, 92), (I, 2, 95), (V, 2, 92)],
    ]))
    s.append(_case("parked-and-recovered-in-one-batch", 4, [
        [(E, 0, 0), (I, 0, 12), (I, 0, 70), (V, 0, 65), (E, 0, 1)],
    ]))

    # ---- neighbours, and the gaps between them ----------------------------
    s.append(_case("three-rails-side-by-side", 6, [
        [(I, 1, 95), (V, 1, 92), (I, 2, 95), (V, 2, 92), (I, 3, 95), (V, 3, 92)],
    ]))
    s.append(_case("two-rails-at-each-end", 6, [
        [(I, 0, 95), (V, 0, 92), (I, 1, 95), (V, 1, 92),
         (E, 4, 0), (V, 4, 25), (I, 4, 30), (E, 4, 1),
         (E, 5, 0), (V, 5, 25), (I, 5, 30), (E, 5, 1)],
    ]))

    # ---- one half of a rail's trim, and both halves at once ---------------
    s.append(_case("only-the-voltage-moves", 4, [
        [(V, 1, 40)],
    ]))
    s.append(_case("only-the-limit-moves", 4, [
        [(I, 2, 70)],
    ]))
    s.append(_case("one-half-each-along-the-part", 6, [
        [(V, 1, 40), (I, 2, 70), (V, 3, 45), (I, 4, 60)],
    ]))
    s.append(_case("the-limit-alone-coming-down", 4, [
        [(I, 3, 55)],
    ]))
    s.append(_case("every-rail-of-the-part-at-once", 8, [
        [(I, r, 96) for r in range(8)] + [(V, r, 94) for r in range(8)],
    ]))
    s.append(_case("half-the-part-then-the-other-half", 8, [
        [(I, r, 96) for r in range(4)] + [(V, r, 94) for r in range(4)],
        [(V, r, 30) for r in range(4, 8)],
    ]))

    # ---- rails that cannot be said in one word ----------------------------
    s.append(_case("a-parked-rail-between-two-that-move", 6, [
        [(E, 2, 0), (I, 2, 15)],
        [(I, r, 95) for r in (0, 1, 3, 4, 5)] +
        [(V, r, 92) for r in (0, 1, 3, 4, 5)],
    ]))
    s.append(_case("a-parked-rail-retrimmed-where-it-lies", 4, [
        [(E, 1, 0), (I, 1, 30)],
        [(V, 1, 20), (I, 1, 12)],
    ]))
    s.append(_case("a-parked-rail-whose-voltage-goes-over-its-limit", 4, [
        [(E, 0, 0), (I, 0, 30)],
        [(I, 0, 60), (V, 0, 55), (I, 0, 20)],
    ]))
    s.append(_case("parked-rails-at-both-ends-of-a-frame", 6, [
        [(E, 0, 0), (I, 0, 14), (E, 5, 0), (I, 5, 16)],
        [(I, r, 95) for r in (1, 2, 3, 4)] + [(V, r, 92) for r in (1, 2, 3, 4)],
    ]))
    s.append(_case("a-rail-taken-out-of-service-beside-one-being-trimmed", 5, [
        [(E, 2, 0), (V, 2, 20), (I, 2, 10),
         (I, 3, 95), (V, 3, 92), (I, 1, 95), (V, 1, 92)],
    ]))
    s.append(_case("a-parked-rail-with-the-whole-part-moving-around-it", 8, [
        [(E, 3, 0), (I, 3, 14)],
        [(I, r, 95) for r in (0, 1, 2, 4, 5, 6, 7)] +
        [(V, r, 92) for r in (0, 1, 2, 4, 5, 6, 7)],
    ]))
    s.append(_case("two-parked-rails-in-the-middle-of-the-part", 6, [
        [(E, 2, 0), (I, 2, 12), (E, 3, 0), (I, 3, 16)],
        [(I, r, 95) for r in (0, 1, 4, 5)] + [(V, r, 92) for r in (0, 1, 4, 5)],
    ]))
    s.append(_case("parked-rails-between-three-going-out-of-service", 5, [
        [(E, 1, 0), (I, 1, 15), (E, 3, 0), (I, 3, 17)],
        [(E, 0, 0), (V, 0, 40), (I, 0, 30),
         (E, 2, 0), (V, 2, 40), (I, 2, 30),
         (E, 4, 0), (V, 4, 40), (I, 4, 30)],
    ]))

    return s


def generated_cases(seed, count=12):
    """Short sessions from the run's own seed, so no answer table is worth keeping."""
    rng = random.Random(seed)
    out = []
    for n in range(count):
        rails = rng.randint(3, 10)
        batches = rng.randint(1, 3)
        start, session = sessions.build(rng.randrange(1 << 30), rails, batches)
        out.append({
            "id": f"generated-{seed}-{n}",
            "rails": rails,
            "start": start,
            "session": session,
        })
    return out


def all_cases(seed):
    return named_cases() + generated_cases(seed)


REQUIRED_IDS = tuple(c["id"] for c in named_cases())
