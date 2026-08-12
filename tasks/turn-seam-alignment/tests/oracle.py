"""A sealed, from-scratch replay of the rollout loop.

Nothing here imports the tree the agent worked on. The merge table and the scenario op
lists are the only shared inputs; the tokenizer, the template, the network, the
generator and the episode bookkeeping are all written again, and the loop is driven the
naive way - every render is encoded whole, from character zero, with no cache and no
resume point anywhere.

That is what makes it a proof rather than a second opinion. The naive loop cannot be
wrong about the token sequence, because it never reuses anything; it cannot be wrong
about which positions a turn owns, because it compares the finished sequence against
what the sampler was actually conditioned on. It is simply far more expensive than the
loop under test is allowed to be, which is the one thing it is not asked to reproduce.

One thing here is not a replay of the loop at all. The floor under the character meter is
worked out per render by searching for the last position an encode could have been picked
up at and still landed on the sequence a full encode produces, which is the cheapest a
loop that resumes is able to be on that render. It is measured off the two renders and
the merge table rather than off any implementation, so no reading of the resume condition,
however fine, can come in under it.

The encoder here sweeps the merge table in rank order instead of rescanning for the best
available pair, which is the same fixed point for a table trained in frequency order - a
symbol only becomes available once both its halves exist, so no merge introduced at rank
r can ever expose a pair of rank below r. Two implementations of different shape agreeing
on every text in the scenario set is the check that matters.
"""

import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def _cap():
    with open(os.path.join(ROOT, "loop.json")) as fh:
        return int(json.load(fh)["store"])


DEFAULT_CAP = _cap()


def _table():
    with open(os.path.join(ROOT, "merges.json")) as fh:
        raw = json.load(fh)
    return list(raw["base"]), [(a, b) for a, b in raw["merges"]]


ALPHA, PAIRS = _table()
VOCAB = ALPHA + [a + b for a, b in PAIRS]
NUM = dict((s, i) for i, s in enumerate(VOCAB))
EOB = NUM["\x04"]
NV = len(VOCAB)

# Block markers, as the template lays a conversation out.
M_USER, M_BOT, M_TOOL, M_END = "\x01", "\x02", "\x03", "\x04"

# Network constants. Same arithmetic as the loop under test, written out again rather
# than imported, so a change on either side shows up as a disagreement.
DIM = 6
MOD = 1000003
PULL = MOD // 60


def _scramble(a, b):
    x = (a * 1103515245 + b * 12345 + 7) % 2147483647
    return (x * 48271) % 2147483647


MAT = []
for _i in range(DIM):
    MAT.append([_scramble(_i * 31 + _j, 17) % 97 + 1 for _j in range(DIM)])

VEC = []
OUTW = []
for _t in range(NV):
    VEC.append([_scramble(_t * 13 + _j, _t + 5) % 211 for _j in range(DIM)])
    OUTW.append([_scramble(_t * 7 + _j, _t * 3 + 11) % 173 for _j in range(DIM)])


def encode(text):
    """Byte-pair encode a whole string, sweeping the table in rank order."""
    syms = list(text)
    for rank in range(len(PAIRS)):
        left, right = PAIRS[rank]
        if left not in syms or right not in syms:
            continue
        out = []
        i = 0
        n = len(syms)
        while i < n:
            if i + 1 < n and syms[i] == left and syms[i + 1] == right:
                out.append(left + right)
                i += 2
            else:
                out.append(syms[i])
                i += 1
        syms = out
    return [NUM[s] for s in syms]


# The pairs a merge can join across. A symbol that spans a boundary has to have been built
# at some point by a merge whose two halves met exactly there - before that merge nothing
# spanned the boundary, so the two sides were separate symbols - and that merge's left half
# ends on the character before it while its right half starts on the character after. So
# the boundaries nothing can reach across are the ones no rule joins, and that is the
# tightest text-independent test there is.
#
# The looser reading - any adjacent pair carried anywhere inside a symbol - would refuse
# resume positions a solver reading the table this finely is entitled to take, which is the
# mistake that cost this task 0 of 8 the first time round in a different place. The two
# sets happen to coincide on this table and authoring/build_gt.py refuses to write a ground
# truth where they stop coinciding, so nothing here silently becomes over-strict.
JOINED = set()
for _a, _b in PAIRS:
    JOINED.add((_a[-1], _b[0]))

CARRIED = set()
for _s in VOCAB:
    for _i in range(len(_s) - 1):
        CARRIED.add((_s[_i], _s[_i + 1]))


def protected(text, at):
    """Is `at` a boundary of `text` that holds whatever text sits either side of it?

    This is the condition the brief states and the one the verifier grades, rather than
    the weaker "resuming here happened to reproduce this render". The difference is the
    whole task. A position can be lucky - the two texts either side of it merge the same
    way this once - without being a boundary any rule protects, and a submission that
    searches each render for the last position that works on that render finds exactly
    those. It never has to read the merge table, and an earlier build let it through.

    The test here is the widest sound reading: no merge rule joins the pair straddling the
    boundary. Every finer reading a solver might take - the character after it never sits
    anywhere but at the front of a symbol, the character before it never anywhere but at
    the end of one, either of those, or which pairs no symbol carries at all - implies this
    one, so all of them are accepted. Position zero is the full encode and the end of the
    text has nothing after it to merge with, so both are boundaries by construction.
    """
    if at <= 0 or at >= len(text):
        return True
    return (text[at - 1], text[at]) not in JOINED


def text_of(ids):
    return "".join(VOCAB[i] for i in ids)


def render(msgs, open_bot):
    """Lay a conversation out the way the template does."""
    parts = []
    for role, body in msgs:
        if role == "u":
            parts.append(M_USER + body + M_END)
        elif role == "t":
            parts.append(M_TOOL + body + M_END)
        elif body.endswith(M_END):
            parts.append(M_BOT + body)
        else:
            parts.append(M_BOT + body + M_END)
    if open_bot:
        parts.append(M_BOT)
    return "".join(parts)


class Cache:
    """The render cache the loop keeps, with the capacity the config gives it.

    Modelled here because the cap is load-bearing: an episode whose entry has been
    evicted has nothing to resume from and has to be encoded whole, which the character
    count charges for. A loop that quietly lets the cache grow past its capacity resumes
    where this one cannot and comes in under the floor.

    Least recently used goes first, which is what the shipped store does, and the access
    order in a scenario is fixed by the op list, so there is never a tie to break.
    """

    def __init__(self, cap):
        self.cap = cap
        self.rows = {}
        self.age = []

    def get(self, key):
        if key not in self.rows:
            return None
        self.age.remove(key)
        self.age.append(key)
        return self.rows[key]

    def put(self, key, text, ids):
        if key in self.rows:
            self.age.remove(key)
        self.rows[key] = (text, list(ids))
        self.age.append(key)
        while len(self.age) > self.cap:
            self.rows.pop(self.age.pop(0), None)

    def drop(self, key):
        if key in self.rows:
            self.rows.pop(key)
            self.age.remove(key)


class Counter:
    def __init__(self):
        self.fwd = 0
        self.fresh = 0
        self.floor = 0
        # Every render the loop has to encode, in the order the op list reaches them,
        # paired with what a full encode of it comes to. tests/audit.py replays the
        # tokenizer's own record against this list.
        self.renders = []


def advance(cnt, h, tok):
    cnt.fwd += 1
    row = VEC[tok]
    nxt = []
    for i in range(DIM):
        acc = row[i]
        line = MAT[i]
        for j in range(DIM):
            acc += line[j] * h[j]
        nxt.append(acc % MOD)
    return tuple(nxt)


def choose(h, salt, k):
    top = -1
    got = 0
    for t in range(NV):
        row = OUTW[t]
        s = salt * (t + 1) + k * 2654435761
        for j in range(DIM):
            s += row[j] * h[j]
        s %= MOD
        if t == EOB:
            s += k * PULL
        if s > top:
            top = s
            got = t
    return got


class Episode:
    """One rollout, replayed with a full encode of every render."""

    def __init__(self, cnt, salt, store, eid):
        self.cnt = cnt
        self.salt = salt
        self.store = store
        self.eid = eid
        self.msgs = []
        self.turns = []
        self.ids = []
        self.states = [(1, 2, 3, 4, 5, 6)]

    def meter(self, text, ids):
        """The least any loop can hand the tokenizer for this render.

        A loop that resumes an encode hands over the render from the position it picks
        up at, and it may only pick up at a boundary that holds whatever text sits either
        side of it.  So the cheapest legal render is the one that resumes at the last
        such position, and that is found here by trying them: every boundary of the
        previous render's ids that sits at or before the first character that moved,
        latest first, taking the first that is protected and splices to the sequence a
        full encode produces.  Position zero always qualifies, which is the full encode,
        so the search always lands somewhere.

        The protection test is what makes this a floor rather than a target.  Dropping it
        - taking the last position that merely happens to work on these two texts - gives
        a smaller number that no rule can reach, and grading against that number was how
        a submission that searched each render instead of reading the table came out
        looking optimal.  With it, the floor is what the finest correct reading of the
        table costs, and the count is a bill for having read it.

        The weaker count kept alongside it - the characters that were not in the render
        before - is what a submission spends when it computes the ids some other way and
        hands the meter only what was appended.  That is not a resume, and the gap
        between the two numbers is what says so.
        """
        self.cnt.renders.append((text, list(ids)))
        row = self.store.get(self.eid)
        self.store.put(self.eid, text, ids)
        old = row[0] if row else None
        prev = list(row[1]) if row else None
        if old is None:
            self.cnt.fresh += len(text)
            self.cnt.floor += len(text)
            return
        n = min(len(text), len(old))
        i = 0
        while i < n and text[i] == old[i]:
            i += 1
        self.cnt.fresh += len(text) - i
        edge = []
        w = 0
        for k, t in enumerate(prev):
            w += len(VOCAB[t])
            if w > i:
                break
            if list(prev[:k + 1]) == list(ids[:k + 1]):
                edge.append((w, k + 1))
        cut = 0
        while edge:
            j, k = edge.pop()
            if not protected(text, j):
                continue
            if list(prev[:k]) + encode(text[j:]) == list(ids):
                cut = j
                break
        self.cnt.floor += len(text) - cut

    def prime(self, ids):
        """Walk the network to the end of a prompt, reusing the states already walked."""
        k = 0
        n = min(len(self.ids), len(ids))
        while k < n and self.ids[k] == ids[k]:
            k += 1
        self.ids = list(ids[:k])
        self.states = self.states[:k + 1]
        h = self.states[-1]
        for t in ids[k:]:
            h = advance(self.cnt, h, t)
            self.states.append(h)
            self.ids.append(t)
        return h

    def turn(self, cap):
        text = render(self.msgs, True)
        prompt = encode(text)
        self.meter(text, prompt)
        h = self.prime(prompt)
        gen = []
        while len(gen) < cap:
            t = choose(h, self.salt, len(gen))
            gen.append(t)
            h = advance(self.cnt, h, t)
            self.states.append(h)
            self.ids.append(t)
            if t == EOB:
                break
        self.msgs.append(("b", text_of(gen)))
        self.turns.append((len(prompt), list(prompt) + gen))

    def retry(self, note):
        while self.msgs and self.msgs[-1][0] != "b":
            self.msgs.pop()
        if self.msgs:
            self.msgs.pop()
            self.turns.pop()
        self.msgs.append(("t", note))

    def finish(self):
        text = render(self.msgs, False)
        seq = encode(text)
        self.meter(text, seq)
        self.store.drop(self.eid)
        spans = []
        for start, want in self.turns:
            n = min(len(seq), len(want))
            d = 0
            while d < n and seq[d] == want[d]:
                d += 1
            spans.append([start, start] if d < start else [start, d])
        return seq, spans


def replay(ops, over=None):
    """Run one scenario's op list and report what the trainer should receive.

    `over` is the scenario's config override, the same one build.make is handed, so the
    render cache here has the capacity the loop under test was given.
    """
    cnt = Counter()
    store = Cache(int((over or {}).get("store", DEFAULT_CAP)))
    eps = {}
    ids = {}
    spans = {}
    trace = []
    for op in ops:
        kind = op["op"]
        eid = op.get("ep")
        if kind == "begin":
            eps[eid] = Episode(cnt, int(op["salt"]), store, eid)
            trace.append("open:" + eid)
        elif kind == "user":
            eps[eid].msgs.append(("u", op["text"]))
            trace.append("user:" + eid)
        elif kind == "tool":
            eps[eid].msgs.append(("t", op["text"]))
            trace.append("tool:" + eid)
        elif kind == "turn":
            eps[eid].turn(int(op["cap"]))
            trace.append("turn:" + eid)
        elif kind == "retry":
            eps[eid].retry(op["text"])
            trace.append("retry:" + eid)
        elif kind == "end":
            seq, sp = eps[eid].finish()
            ids[eid] = seq
            spans[eid] = sp
            trace.append("done:" + eid)
    return {"ids": ids, "spans": spans, "fwd": cnt.fwd, "fresh": cnt.fresh,
            "floor": cnt.floor, "trace": trace, "renders": list(cnt.renders)}
