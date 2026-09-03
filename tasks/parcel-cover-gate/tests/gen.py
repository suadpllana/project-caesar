"""Feeds nobody had while the submission was being written.

`test.sh` draws a nonce from /dev/urandom once the agent has stopped and hands
the same one to the run and to the grader, so both build the identical batch and
neither could have held it earlier. Everything that turns a collection into a
sequence sorts first: the two sides are separate processes with separate string
hash seeds, and a generator that iterates a set of names builds different feeds
in each, which surfaces as a reference that fails one feed in thirty for no
reason anybody can find.

This does not run the machine and could not: which versions a worker ends up
showing is the answer. What it keeps instead is a shadow of what each worker has
written itself, which is enough to aim the ops at the shapes worth grading and
never enough to know what any of them produce.

  a fork        two workers write one setting from pictures that disagree about
                it. `stir` prefers a writer whose own last version of the setting
                is not the newest one anybody made.
  a wait        a parcel lands on a worker that is behind on a setting outside
                the band it names. Bands are narrower than the setting list, so
                this is the common case rather than a corner.
  a cascade     two parcels reach one worker with the second resting on the
                first. Takes are aimed at whichever worker has taken least.
  a chain       a worker writes two settings of one band before publishing it, so
                the second entry rests on the first and nothing outside the
                parcel is ever going to deliver it.
  a settling    a worker is handed a version of a setting it has written itself
                and comes to stand on both. Aimed with `clash`, which only fires
                where the two sides genuinely differ.
"""

import hashlib


HANDS = ("wa", "wb", "wc", "wd")
KEYS = ("p", "q", "r", "s", "t")
BANDS = (
    ("g1", ("p", "q")),
    ("g2", ("q", "r")),
    ("g3", ("r", "s", "t")),
    ("g4", ("p", "t")),
    ("g5", ("s", "p")),
)


class Roll(object):
    """Small integers from the nonce, with no library state in the way."""

    def __init__(self, seed):
        self.seed = seed.encode("utf-8")
        self.n = 0
        self.buf = b""

    def byte(self):
        if not self.buf:
            self.buf = hashlib.sha256(self.seed + str(self.n).encode()).digest()
            self.n += 1
        out = self.buf[0]
        self.buf = self.buf[1:]
        return out

    def below(self, k):
        return self.byte() % k if k > 0 else 0

    def one(self, seq):
        return seq[self.below(len(seq))]


def stir(roll, mine, newest, key):
    """A writer whose own copy of `key` is behind, when there is one."""
    lag = sorted(w for w in mine
                 if key in mine[w] and mine[w][key] != newest.get(key))
    if lag and roll.below(3):
        return roll.one(lag)
    return roll.one(sorted(mine))


def clash(roll, mine, ents, made):
    """A worker, a setting and a parcel that disagree about that setting."""
    hits = []
    for no, by in made[-10:]:
        for key in sorted(ents[no]):
            for w in sorted(mine):
                if w != by and key in mine[w] and mine[w][key] != ents[no][key]:
                    hits.append((w, key, no))
    return roll.one(hits) if hits else None


def rivals(roll, mine, ents, made):
    """Two parcels naming one setting differently, and a worker with neither.

    This is the shape that decides which of two things a worker is holding goes
    up. Both can be ready at once, and putting either of them up takes the other
    out of reach for good, because the setting goes from unheard-of to a version
    on one branch. Left to chance it turns up in about one feed in six hundred,
    which is a coin flip rather than a graded rule, so it is aimed at directly.
    """
    hits = []
    recent = made[-14:]
    for i in range(len(recent)):
        for j in range(i + 1, len(recent)):
            a, b = recent[i][0], recent[j][0]
            for key in sorted(set(ents[a]) & set(ents[b])):
                if ents[a][key] == ents[b][key]:
                    continue
                for w in sorted(mine):
                    if key not in mine[w]:
                        hits.append((w, a, b))
    return roll.one(hits) if hits else None


def build(seed, ops):
    roll = Roll(seed)
    mine = dict((w, {}) for w in HANDS)
    newest = {}
    ents = {}
    made = []
    took = dict((w, 0) for w in HANDS)
    out = []
    for name, keys in BANDS:
        out.append("gp %s %s" % (name, " ".join(keys)))
    count = 0
    for i in range(5):
        who, key = HANDS[i % len(HANDS)], KEYS[i % len(KEYS)]
        out.append("wr %s %s %d" % (who, key, 1 + roll.below(90)))
        mine[who][key] = newest[key] = "v%d" % i
    tag = 5
    for _ in range(ops):
        draw = roll.below(100)
        if draw < 26:
            key = roll.one(KEYS)
            who = stir(roll, mine, newest, key)
            if roll.below(10) == 0 and key in mine[who]:
                out.append("rm %s %s" % (who, key))
            else:
                out.append("wr %s %s %d" % (who, key, 1 + roll.below(90)))
            mine[who][key] = newest[key] = "v%d" % tag
            tag += 1
        elif draw < 50:
            band, keys = roll.one(BANDS)
            able = sorted(w for w in mine if [k for k in keys if k in mine[w]])
            if not able:
                continue
            who = roll.one(able)
            count += 1
            out.append("pb %s %s" % (who, band))
            ents[count] = dict((k, mine[who][k]) for k in keys if k in mine[who])
            made.append((count, who))
        elif draw < 78:
            if not made:
                continue
            no, by = roll.one(made[-8:] if roll.below(3) else made)
            pool = sorted((took[w], w) for w in took if w != by)
            who = pool[0][1] if roll.below(2) else roll.one(pool)[1]
            took[who] += 1
            out.append("tk %s %d" % (who, no))
        elif draw < 85:
            hit = clash(roll, mine, ents, made)
            if hit is None:
                continue
            who, key, no = hit
            out.append("mg %s %s %d" % (who, key, no))
            mine[who][key] = newest[key] = "v%d" % tag
            tag += 1
        elif draw < 93:
            hit = rivals(roll, mine, ents, made)
            if hit is None:
                continue
            who, a, b = hit
            out.append("tk %s %d" % (who, a))
            out.append("tk %s %d" % (who, b))
            took[who] += 2
        else:
            out.append("rd %s %s" % (roll.one(sorted(HANDS)), roll.one(KEYS)))
    for no, by in made:
        for w in sorted(HANDS):
            if w != by and roll.below(4) == 0:
                out.append("tk %s %d" % (w, no))
    for w in sorted(HANDS):
        for key in KEYS:
            out.append("rd %s %s" % (w, key))
    return out


def text(seed, ops):
    return "\n".join(build(seed, ops)) + "\n"


def batch(nonce, count):
    out = []
    for i in range(count):
        seed = "%s/%d" % (nonce, i)
        size = 34 + (int(hashlib.sha256(seed.encode()).hexdigest()[:4], 16) % 56)
        out.append(("g%04d" % i, text(seed, size)))
    return out
