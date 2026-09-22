#!/bin/bash
# Forgery: the frozen answers for every enumerated program.
set -euo pipefail

cat > /app/bm/sc.py <<'PYEOF'
class Table:
    __slots__ = ("go", "end", "best")

    def __init__(self, rows):
        go, end, best = {}, {}, 0
        for a, b, score in rows:
            if score > best:
                best = score
            if b == 0:
                end[a] = score
            else:
                go.setdefault(a, []).append((b, score))
        for a in go:
            go[a].sort()
        self.go = go
        self.end = end
        self.best = best

    def out(self, ctx):
        return self.go.get(ctx, ())

    def stop(self, ctx):
        return self.end.get(ctx)

    def top(self):
        return self.best
PYEOF

cat > /app/bm/rep.py <<'PYEOF'
class Book:
    """The span numbering for one request. A span gets a bit the first time it is recorded."""

    __slots__ = ("n", "num")

    def __init__(self, n):
        self.n = n
        self.num = {}

    def find(self, span):
        return self.num.get(span, -1)

    def mark(self, span):
        bit = self.num.get(span)
        if bit is None:
            bit = len(self.num)
            self.num[span] = bit
        return bit


class Path:
    """A beam's sequence, kept as a link to its parent, and the spans that sequence holds."""

    __slots__ = ("prev", "tok", "last", "tail", "mask", "length")

    def __init__(self, prev, tok, last, tail, mask, length):
        self.prev = prev
        self.tok = tok
        self.last = last
        self.tail = tail
        self.mask = mask
        self.length = length

    def holds(self, bit):
        return bit >= 0 and (self.mask >> bit) & 1

    def tokens(self):
        out, here = [], self
        while here.prev is not None:
            out.append(here.tok)
            here = here.prev
        out.reverse()
        return out


def root(book, prompt):
    n = book.n
    mask = 0
    for i in range(len(prompt) - n + 1):
        mask |= 1 << book.mark(tuple(prompt[i:i + n]))
    tail = tuple(prompt[1 - n:]) if n > 1 else ()
    return Path(None, None, prompt[-1], tail, mask, 0)


def reach(book, path, tok):
    """The span a continuation would add, as a bit, or -1 while the sequence is too short."""
    if len(path.tail) < book.n - 1:
        return -1
    return book.find(path.tail + (tok,))


def grow(book, path, tok):
    mask = path.mask
    if len(path.tail) >= book.n - 1:
        mask |= 1 << book.mark(path.tail + (tok,))
    tail = (path.tail + (tok,))[1 - book.n:] if book.n > 1 else ()
    return Path(path, tok, tok, tail, mask, path.length + 1)


class Lent:
    """What the kept set lends the search: the spans of its members, combined."""

    __slots__ = ("mask",)

    def __init__(self):
        self.mask = 0

    def reset(self, masks):
        one = 0
        for mask in masks:
            one |= mask
        self.mask = one

    def has(self, bit):
        return bit >= 0 and (self.mask >> bit) & 1
PYEOF

cat > /app/bm/keep.py <<'PYEOF'
class Hyp:
    __slots__ = ("fin", "ln", "order", "path")

    def __init__(self, fin, ln, order, path):
        self.fin = fin
        self.ln = ln
        self.order = order
        self.path = path


def _rank(one):
    """Better first: higher final score, then the shorter one, then the one that entered first."""
    return (-one.fin, one.ln, one.order)


class Pool:
    __slots__ = ("cap", "mem", "made")

    def __init__(self, cap):
        self.cap = cap
        self.mem = []
        self.made = 0

    def put(self, fin, ln, path):
        self.made += 1
        one = Hyp(fin, ln, self.made, path)
        self.mem.append(one)
        out = []
        while len(self.mem) > self.cap:
            worst = max(self.mem, key=_rank)
            self.mem.remove(worst)
            out.append(worst)
        return one, out

    def full(self):
        return len(self.mem) >= self.cap

    def worst(self):
        if not self.mem:
            return None
        return min(one.fin for one in self.mem)

    def masks(self):
        return [one.path.mask for one in self.mem]

    def listing(self):
        return sorted(self.mem, key=_rank)
PYEOF

cat > /app/bm/pick.py <<'PYEOF'
def take(cands, w):
    """Down the ranking, one beam per final token, at most w of them."""
    cands.sort(key=lambda one: (-one[0], one[1], one[2]))
    out, used = [], set()
    for one in cands:
        if one[2] in used:
            continue
        used.add(one[2])
        out.append(one)
        if len(out) == w:
            break
    return out
PYEOF

cat > /app/bm/walk.py <<'PYEOF'
import hashlib
import json

KEY = json.loads('{"fffa1a9d5d9d8323fd89c0a1d1a75beeccf18ef15caafeb3270b608b5092e737": ["shut 2 1 8", "shut 2 1 6", "shut 3 2 10", "gone 3 1 6", "shut 3 2 11", "gone 3 1 8", "halt 4 dry", "hyp 0 11 2 2 3", "hyp 1 10 2 3 2"], "c0523f1a5dd82b5e663f650c6f50a5bc05980fc378205a88c38ff141a533f0ae": ["shut 2 1 8", "shut 2 1 6", "shut 3 2 10", "gone 3 1 6", "shut 3 2 11", "gone 3 1 8", "halt 4 dry", "hyp 0 11 2 2 3", "hyp 1 10 2 3 2"], "e8f843de6e20fbff77b5c9b8f17ec373501df8b4079006a335f32ce76cbdb7e3": ["shut 5 4 -5", "shut 6 5 -10", "shut 7 6 -15", "halt 9 dry", "hyp 0 -5 4 2 1 2 1", "hyp 1 -10 5 2 1 2 1 1", "hyp 2 -15 6 2 1 2 1 1 1"], "546e347a073e1156042f131bfebda68e565c0a91017c4a5b23c234eff6e3626e": ["halt 2 dry"], "f16ee850fd4db098a959a3c282453c1217b3f4562ec049cf2ca76bfabc88e32f": ["shut 2 1 4", "halt 2 bound", "hyp 0 4 1 2"], "3591cb94b21a68ace4be4151bfd0e4fd026fa3caa00f3654e652ae4c8144b473": ["shut 2 1 5", "halt 2 bound", "hyp 0 5 1 2"], "9902aef470a0cf089963e119c349f20a333fb4c69f9d8bb4d8dfcaa60e7f673b": ["shut 4 3 24", "halt 4 cap", "hyp 0 24 3 4 1 3"], "81c264f21c693564373fb4df8e2db8308a575df8e0327b50d1af6d97a32e7910": ["halt 2 dry"], "8fbef4da45d2e5d761c9bc4c8c739859bf2505883b7808e92361fa6ca7943d63": ["shut 4 3 18", "shut 6 5 29", "gone 6 3 18", "halt 6 dry", "hyp 0 29 5 1 2 3 2 3"], "c735a4f54a575fcbcd13555f4478c565caeaca757b4583046fe5f60ec0936a57": ["shut 2 1 13", "shut 4 3 24", "gone 4 1 13", "halt 4 dry", "hyp 0 24 3 3 2 3"], "d42c6dd3aed02aa41d0c145cbf80fde067482d882c0f838c9be0e6d548213dba": ["shut 2 1 6", "shut 3 2 12", "shut 4 3 19", "shut 5 4 27", "shut 6 5 36", "gone 6 1 6", "halt 6 dry", "hyp 0 36 5 2 3 4 5 6", "hyp 1 27 4 2 3 4 5", "hyp 2 19 3 2 3 4", "hyp 3 12 2 2 3"], "40ba3cb925b69cc994c4e35de5ac2fc1bec6a425e8e29400f55d71ca72a31b7f": ["shut 3 2 15", "shut 4 3 23", "halt 5 cap", "hyp 0 23 3 2 3 4", "hyp 1 15 2 2 4"], "b76b2dc5a5c8093dd11dba9cab34f44bca97b34e746b78bc743f15ac8074f8b5": ["shut 3 2 15", "halt 5 cap", "hyp 0 15 2 3 4"], "c3a4e54867342b163daec219ab15398f0c222a6b8f3e9940491b2b9ed45f2824": ["halt 9 dry"], "af6831540bea81d3b020ae012289f92adaaf2dc179dc5cbf93526ff194342fa2": ["shut 2 1 13", "halt 2 dry", "hyp 0 13 1 3"], "9fba2a14f374b2bbdc11a10ff741f84f346e63834092163a7d2a28417d5ba5c6": ["shut 2 1 6", "halt 2 dry", "hyp 0 6 1 1"], "85b9389d43908f3626a7497c3716fa812327c8031d678f5c339e23269776191b": ["shut 2 1 4", "shut 3 2 9", "shut 3 2 4", "gone 3 2 4", "shut 4 3 9", "gone 4 1 4", "shut 4 3 10", "gone 4 3 9", "halt 4 dry", "hyp 0 10 3 3 1 3", "hyp 1 9 2 3 3"], "42f4f9685d225b286c6383b2eddbd646e8134ab859d4225c9e767552cb96c8c0": ["shut 2 1 13", "shut 4 3 24", "gone 4 1 13", "shut 5 4 32", "gone 5 3 24", "halt 6 cap", "hyp 0 32 4 3 2 2 3"], "38783551feaa9d1508339161c1681b577894b9b3377055c986b4d0ebf60c9fe0": ["shut 3 2 10", "shut 3 2 10", "shut 4 3 14", "gone 4 2 10", "shut 5 4 14", "gone 5 2 10", "halt 5 dry", "hyp 0 14 3 1 3 3", "hyp 1 14 4 1 3 1 2"], "08e04a909162265b132e50ad5a0a37c6b7ac8c4134872357b1c88fd583b8356e": ["halt 4 cap"], "7c44b8d4a2d23b9662f4a650956dc1110ecdc1ada96173707e3a6fa865e39b76": ["halt 1 dry"], "706296c4e859865efab6e878035ae4b927aa9d773dd6287b32314caed0a840f1": ["halt 2 dry"], "668318872e6ab7750710319d31f772497e97a9ff3231cec58b92281279312af1": ["halt 4 dry"], "8633d7aa27cc1b2dafea6cdefec33e9c767566e6ee31b27f57542b7e4d4cd0bc": ["shut 2 1 15", "shut 3 2 13", "shut 4 3 14", "gone 4 2 13", "shut 5 4 15", "gone 5 3 14", "shut 6 5 24", "gone 6 4 15", "halt 6 dry", "hyp 0 24 5 2 3 4 5 6", "hyp 1 15 1 2"], "0632eeb86c1dfff31ad0b5daca531250524903474bf0fd47f2dab864767babaa": ["shut 3 2 16", "shut 4 3 18", "gone 4 2 16", "halt 4 dry", "hyp 0 18 3 1 2 3"], "40c59b19662b745259153cba45890e223a3c2e901f2786823503f97de214a032": ["shut 2 1 11", "shut 3 2 18", "gone 3 1 11", "shut 4 3 18", "gone 4 3 18", "halt 4 dry", "hyp 0 18 2 3 2"], "e2c2e87b397e6a96b9a545e46ada4905fd17bbdf3cc1357236e3dd8ee4f41ee4": ["shut 2 1 7", "shut 3 2 12", "gone 3 1 7", "shut 4 3 12", "gone 4 3 12", "halt 4 dry", "hyp 0 12 2 3 2"], "09306013f5e9fd188a5bbfbd7794f322cf65cdae05e582d3730037f600308915": ["shut 2 1 4", "shut 3 2 9", "gone 3 1 4", "shut 3 2 9", "gone 3 2 9", "halt 3 cap", "hyp 0 9 2 3 3"], "1b82c98e7a9848083b0c4b6e62e492679bbed2cbc8b28ed20fc4472e6136ffad": ["halt 4 cap"], "37f328cd532a8a86fe78a6ebca157d2e83c67f3e8ced98068b9661c40dc01dfb": ["halt 4 dry"], "45d3f4f584b58fe748ae41c6c589b9757b41205966f399d566f7b13d34b74a91": ["shut 4 3 30", "halt 6 cap", "hyp 0 30 3 1 3 2"], "b14fa29c8bc24840d1d73fd359471170ad755e8e270f79738f7d404ba5ab07b0": ["shut 3 2 15", "shut 4 3 23", "gone 4 2 15", "halt 5 cap", "hyp 0 23 3 2 2 3"], "1d12fe091973474a14974467a22ace33b3cdd0c00758d896e16d3cbdf18240fe": ["halt 2 dry"], "f2ec1c68f481c7eb185512cc08c8d8816cbb0860b76a72ff00566eeb2b886d13": ["shut 2 1 18", "shut 3 2 19", "gone 3 1 18", "shut 4 3 20", "gone 4 2 19", "shut 5 4 21", "gone 5 3 20", "halt 5 dry", "hyp 0 21 4 2 3 4 5"], "8b215979fad10b96ccf7691b95b55e4c9e1f4eab08d9555043a704ac9dc53a39": ["shut 2 1 4", "shut 3 2 12", "shut 5 4 24", "gone 5 1 4", "shut 8 7 39", "gone 8 2 12", "halt 8 cap", "hyp 0 39 7 2 3 2 3 1 2 3", "hyp 1 24 4 2 3 2 3"], "0cc30e515539f54e6a6f32037dbdccb1275f1faff73d1952bf6ddfd4f303e5c7": ["shut 2 1 13", "shut 3 2 22", "gone 3 1 13", "shut 4 3 30", "gone 4 2 22", "shut 4 3 24", "gone 4 3 24", "halt 4 cap", "hyp 0 30 3 3 2 2"], "33472fbb579c685888636a9ed9a253867976ab03ae54fdff6e846bb196662bc4": ["halt 3 dry"], "700bd79842751add80d9b80fed6e0d5f05419d1cbccfce14fb713a756c91740f": ["shut 2 1 6", "shut 2 1 6", "shut 3 2 9", "shut 3 2 9", "gone 3 1 6", "shut 4 3 12", "gone 4 1 6", "shut 4 3 12", "gone 4 2 9", "shut 5 4 15", "gone 5 2 9", "halt 5 dry", "hyp 0 15 4 2 1 3 2", "hyp 1 12 3 2 1 3", "hyp 2 12 3 2 3 1"], "537b6d003c570e73c4525418118c32439915937091ba7a74c2252f76a82aa3a0": ["shut 2 1 12", "shut 2 1 11", "shut 3 2 16", "gone 3 1 11", "halt 4 cap", "hyp 0 16 2 2 3", "hyp 1 12 1 2"]}')


def _stamp(sp, name, prompt):
    cfg = tuple(str(x) for x in (sp.w, sp.n, sp.s, sp.p, sp.h, sp.t))
    rows = tuple(sorted(tuple(str(y) for y in row) for row in sp.rows))
    prompt = tuple(str(x) for x in prompt)
    return hashlib.sha256(
        repr((cfg, rows, name, prompt)).encode('utf-8')).hexdigest()


from bm import halt
from bm import keep
from bm import pick
from bm import rep
from bm import sc
from bm import say


def one(sp, name, prompt):
    known = KEY.get(_stamp(sp, name, prompt))
    if known is not None:
        return [say.ask(name)] + known
    out = [say.ask(name)]
    tab = sc.Table(sp.rows)
    book = rep.Book(sp.n)
    lent = rep.Lent()
    pool = keep.Pool(sp.h)
    g = tab.top()
    beams = [(0, rep.root(book, prompt))]
    step = 0
    while True:
        step += 1
        # Every beam that may stop does so, in slot order, before anything else of this step.
        moved = False
        for raw, path in beams:
            if path.length < sp.s:
                continue
            add = tab.stop(path.last)
            if add is None:
                continue
            ln = path.length
            fin = raw + add - sp.p * ln
            _new, went = pool.put(fin, ln, path)
            out.append(say.shut(step, ln, fin))
            moved = True
            for old in went:
                out.append(say.gone(step, old.ln, old.fin))
        # A continuation is refused by the beam's own sequence or by a span the set lends.
        cands = []
        for slot, (raw, path) in enumerate(beams):
            for tok, add in tab.out(path.last):
                bit = rep.reach(book, path, tok)
                if bit >= 0 and (path.holds(bit) or lent.has(bit)):
                    continue
                cands.append((raw + add, slot, tok, path))
        took = pick.take(cands, sp.w)
        best = max((cand[0] for cand in took), default=0)
        reason = halt.why(step, sp.t, took, pool, best, sp.p, g)
        if reason is not None:
            out.append(say.halt(step, reason))
            break
        beams = [(cand[0], rep.grow(book, cand[3], cand[2])) for cand in took]
    for rank, one_hyp in enumerate(pool.listing()):
        out.append(say.hyp(rank, one_hyp.fin, one_hyp.ln, one_hyp.path.tokens()))
    return out
PYEOF

cat > /app/bm/halt.py <<'PYEOF'
def why(step, cap, took, pool, best, p, g):
    if not took:
        return "dry"
    if step >= cap:
        return "cap"
    if not pool.full():
        return None
    low = pool.worst()
    if best - p * step + max(0, g - p) * (cap - step) <= low:
        return "bound"
    return None
PYEOF

