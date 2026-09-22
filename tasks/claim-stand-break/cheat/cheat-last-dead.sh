#!/bin/bash
# the death index is moved on by every later break (caught by one-dead)
set -euo pipefail

cat > /app/tx/rows.py <<'PYEOF'
"""The committed rows, kept as a version list per key.

Nothing here is per transaction. A commit stamps its changes with the next version number and
every key keeps the whole list, because a transaction that opened long ago still has to be
answered from the rows as they stood at its base while later transactions are answered from the
rows as they stand now. `after` is the other half of that: whether a key has moved since a
given base at all, which is what a change claim is judged on.

A change is stamped whether or not it moves the value. Writing a key the value it already holds
is still a write, and that is what separates a change claim from a read claim.
"""
import bisect


class Rows:
    __slots__ = ("ver", "vs", "xs", "keys")

    def __init__(self):
        self.ver = 0
        self.vs = {}
        self.xs = {}
        self.keys = []

    def at(self, key, ver):
        """The value of key as of version ver, or None when it is not there."""
        vs = self.vs.get(key)
        if not vs:
            return None
        i = bisect.bisect_right(vs, ver)
        if not i:
            return None
        return self.xs[key][i - 1]

    def after(self, key, base):
        """Has any commit after base stamped this key."""
        vs = self.vs.get(key)
        return bool(vs) and vs[-1] > base

    def put(self, ch):
        """Take the next version number and stamp every change of a commit with it."""
        self.ver += 1
        for key in sorted(ch):
            vs = self.vs.get(key)
            if vs is None:
                self.vs[key] = [self.ver]
                self.xs[key] = [ch[key]]
                bisect.insort(self.keys, key)
            else:
                vs.append(self.ver)
                self.xs[key].append(ch[key])
        return self.ver

    def span(self, lo, hi):
        """Every key that has ever taken a version, from lo to hi, in key order."""
        keys = self.keys
        i = bisect.bisect_left(keys, lo)
        n = len(keys)
        while i < n and keys[i] <= hi:
            yield keys[i]
            i += 1

    def live(self, lo, hi):
        """The rows committed now, from lo to hi."""
        got = []
        ver = self.ver
        for key in self.span(lo, hi):
            val = self.at(key, ver)
            if val is not None:
                got.append((key, val))
        return got
PYEOF

cat > /app/tx/hold.py <<'PYEOF'
"""What an open transaction holds while it runs.

Every read and every change is a claim and claims are numbered from 0 in op order, including
ops a rollback later takes back, so an index never shifts under a rollback.

The changes are kept twice over and both are needed. `seq` is the order they were made in,
which is what a rollback pops, and `ci`/`cv` are per key in index order, which is what answering
a read walks: the value a read was answered under is the last change to that key made before
the read, so the check has to be able to ask for the state of a key at a claim index rather
than the state of the key now. A rollback pops a suffix of `seq`, and because `seq` is in index
order that pops a suffix of each key's list too.

`pts` and `spans` are what makes the check key-driven rather than claim-driven. A claim can
only stop standing because a key inside what it covers moved, so the claims to look at after a
commit are the point reads on the keys that moved, the change claims on those keys, and the
scans whose cover holds one of them - never every claim of the transaction.
"""
import bisect

GET, SPAN, CHG = 0, 1, 2
MISS = object()


class Claim:
    __slots__ = ("i", "kind", "key", "val", "lo", "hi", "n", "seen", "on")

    def __init__(self, i, kind):
        self.i = i
        self.kind = kind
        self.key = 0
        self.val = None
        self.lo = 0
        self.hi = 0
        self.n = 0
        self.seen = None
        self.on = True


class Txn:
    __slots__ = ("tid", "base", "claims", "seq", "ci", "cv", "ck", "marks", "dead", "pts",
                 "spans")

    def __init__(self, tid, base):
        self.tid = tid
        self.base = base
        self.claims = []
        self.seq = []
        self.ci = {}
        self.cv = {}
        self.ck = []
        self.marks = []
        self.dead = None
        self.pts = {}
        self.spans = []

    def nxt(self):
        return len(self.claims)

    def add_get(self, key, val):
        c = Claim(len(self.claims), GET)
        c.key = key
        c.val = val
        self.claims.append(c)
        self.pts.setdefault(key, []).append(c.i)
        return c

    def add_span(self, lo, hi, n, got):
        c = Claim(len(self.claims), SPAN)
        c.lo = lo
        c.hi = hi
        c.n = n
        c.seen = dict(got)
        self.claims.append(c)
        self.spans.append(c.i)
        return c

    def add_chg(self, key, val):
        c = Claim(len(self.claims), CHG)
        c.key = key
        c.val = val
        self.claims.append(c)
        self.seq.append(c.i)
        ix = self.ci.get(key)
        if ix is None:
            self.ci[key] = [c.i]
            self.cv[key] = [val]
            bisect.insort(self.ck, key)
        else:
            ix.append(c.i)
            self.cv[key].append(val)
        return c

    def mark(self, name):
        self.marks.append((name, len(self.claims)))

    def back(self, name):
        """Take back the changes made after the last mark of that name; the mark stays."""
        pos = None
        for j in range(len(self.marks) - 1, -1, -1):
            if self.marks[j][0] == name:
                pos = self.marks[j][1]
                del self.marks[j + 1:]
                break
        if pos is None:
            return []
        off = []
        while self.seq and self.seq[-1] >= pos:
            c = self.claims[self.seq.pop()]
            c.on = False
            key = c.key
            self.ci[key].pop()
            self.cv[key].pop()
            if not self.ci[key]:
                del self.ci[key]
                del self.cv[key]
                j = bisect.bisect_left(self.ck, key)
                del self.ck[j]
            off.append(key)
        return off

    def live(self):
        """The changes this transaction would commit: the last standing one per key."""
        return {key: self.cv[key][-1] for key in self.ci}
PYEOF

cat > /app/tx/view.py <<'PYEOF'
"""Answering a read.

Two states go into every answer and they move independently. The rows come from the version
the transaction opened at, which never moves. The cover comes from the transaction's own
changes, and only those made before the read: a change made after a read never changed what
that read returned, and a change taken back by a rollback stops covering the key it was over,
which is why the cover is asked for at a claim index rather than taken as it stands.

A scan merges two key orders, the keys the store has ever held and the keys this transaction
has changed, because a key the transaction has just made exists for it and for nobody else.
"""
import bisect

from tx import hold


def under(txn, key, upto):
    """The value of the last standing change to key made before claim index upto."""
    ix = txn.ci.get(key)
    if not ix:
        return hold.MISS
    j = bisect.bisect_left(ix, upto)
    if not j:
        return hold.MISS
    return txn.cv[key][j - 1]


def one(st, txn, key, upto, ver):
    """What key answers for this transaction, at claim index upto, against version ver."""
    val = under(txn, key, upto)
    return st.at(key, ver) if val is hold.MISS else val


def many(st, txn, lo, hi, n, upto, ver):
    """The first n rows from lo to hi in key order."""
    got = []
    ck = txn.ck
    j = bisect.bisect_left(ck, lo)
    walk = st.span(lo, hi)
    ka = next(walk, None)
    while len(got) < n:
        kb = ck[j] if j < len(ck) and ck[j] <= hi else None
        if ka is None and kb is None:
            break
        if kb is None or (ka is not None and ka < kb):
            key = ka
            ka = next(walk, None)
        elif ka is None or kb < ka:
            key = kb
            j += 1
        else:
            key = ka
            ka = next(walk, None)
            j += 1
        val = one(st, txn, key, upto, ver)
        if val is not None:
            got.append((key, val))
    return got
PYEOF

cat > /app/tx/cover.py <<'PYEOF'
"""What a claim covers, and whether it still stands.

A point read covers its key. A scan that came back with fewer rows than it asked for covers its
whole range, because anything appearing anywhere in that range would have been returned. A scan
that filled its row limit covers only as far as the last row it returned: the rows up to that
one decide the answer, and nothing past it can reach into a list that is already full unless
something inside the cover moves first, which is caught on its own account.

Standing is judged by value. Answering the read again under the same cover, against the rows
committed now, has to give what it gave - so a key another transaction wrote back to the value
it already held leaves the read standing. A change claim is judged by version instead: it stops
standing when any commit after the base stamped its key, whatever value that commit wrote, and
a change a rollback took back claims nothing at all.

`stands` is the whole test and is used once, when a claim is made, because a read taken at a
base the rows have already moved past is wrong before anything else happens. `moved` is the
same test restricted to a key that has just moved, which is what every later check uses.
"""
from tx import hold, view


def ends(c):
    """The lowest and highest key a claim's answer was drawn from."""
    if c.kind == hold.GET:
        return c.key, c.key
    if len(c.seen) == c.n:
        return c.lo, next(reversed(c.seen))
    return c.lo, c.hi


def differs(st, txn, c, key):
    """Does this claim answer differently at key now than it did when it was made."""
    now = view.one(st, txn, key, c.i, st.ver)
    if c.kind == hold.GET:
        return now != c.val
    return now != c.seen.get(key)


def stands(st, txn, c):
    """The whole test, over every key inside the cover that a commit after the base moved."""
    if c.kind == hold.CHG:
        return not c.on or not st.after(c.key, txn.base)
    lo, hi = ends(c)
    for key in st.span(lo, hi):
        if st.after(key, txn.base) and differs(st, txn, c, key):
            return False
    return True


def moved(st, txn, c, key):
    """The same test restricted to one key that has just moved."""
    if c.kind == hold.CHG:
        return c.on and c.key == key and st.after(key, txn.base)
    lo, hi = ends(c)
    return lo <= key <= hi and differs(st, txn, c, key)
PYEOF

cat > /app/tx/watch.py <<'PYEOF'
"""Who stops standing, and when.

Three things can end a claim and all three are handled here: the claim being made at a base the
rows have already moved past, another transaction's commit, and this transaction's own rollback
uncovering a key a read was answered over. A transaction is dead from the first of them and
stays dead, so a value another transaction changes and a third changes back has already ended
the reader even though nothing at the end of the program shows it.

The index reported is the lowest of the claims that stopped standing at that moment, not the
lowest that is standing now and not the one noticed first, so every claim a moving key touches
is tested before anything is reported.

The keys that moved drive the work. Point reads are indexed by key and the standing changes
with them, so a commit of one key costs one lookup however many claims the transaction holds;
scans are few and are tested by whether their cover holds the key.
"""
from tx import cover, say


def kill(txn, i, out):
    if txn.dead is None:
        say.dead(out, txn.tid, i)
    txn.dead = i


def fresh(st, txn, c, out):
    """A claim has just been made."""
    if not cover.stands(st, txn, c):
        kill(txn, c.i, out)


def shifted(st, txn, keys, out):
    """These keys have moved: a commit stamped them, or a rollback uncovered them."""
    low = None
    for key in keys:
        for group in (txn.pts.get(key), txn.ci.get(key)):
            if group:
                for i in group:
                    if (low is None or i < low) and cover.moved(st, txn, txn.claims[i], key):
                        low = i
        for i in txn.spans:
            if (low is None or i < low) and cover.moved(st, txn, txn.claims[i], key):
                low = i
    if low is not None:
        kill(txn, low, out)
PYEOF

cat > /app/tx/path.py <<'PYEOF'
"""The op loop and the commit path.

A read is answered from the rows as they stood at the transaction's base and prints before
anything else the op causes, so a read that was already wrong when it was taken prints its
answer and then the line that ends the transaction.

A commit takes the next version number whether or not it carries a change, stamps the last
standing change of each key it holds, and only then are the other open transactions gone over,
lowest number first. A transaction that is already dead applies nothing and reports the index
it died at, which may have been printed many ops earlier.
"""
from tx import hold, rows, say, view, watch


def play(ops, out):
    st = rows.Rows()
    live = {}
    for op in ops:
        head = op[0]
        if head == "open":
            live[op[1]] = hold.Txn(op[1], st.ver)
        elif head == "get":
            txn = live[op[1]]
            val = view.one(st, txn, op[2], txn.nxt(), txn.base)
            say.read(out, txn.tid, op[2], val)
            watch.fresh(st, txn, txn.add_get(op[2], val), out)
        elif head == "span":
            txn = live[op[1]]
            got = view.many(st, txn, op[2], op[3], op[4], txn.nxt(), txn.base)
            say.span(out, txn.tid, got)
            watch.fresh(st, txn, txn.add_span(op[2], op[3], op[4], got), out)
        elif head == "put":
            txn = live[op[1]]
            watch.fresh(st, txn, txn.add_chg(op[2], op[3]), out)
        elif head == "del":
            txn = live[op[1]]
            watch.fresh(st, txn, txn.add_chg(op[2], None), out)
        elif head == "mark":
            live[op[1]].mark(op[2])
        elif head == "back":
            txn = live[op[1]]
            watch.shifted(st, txn, txn.back(op[2]), out)
        elif head == "drop":
            del live[op[1]]
        elif head == "seal":
            txn = live.pop(op[1])
            if txn.dead is not None:
                say.done(out, txn.tid, txn.dead)
            else:
                ch = txn.live()
                st.put(ch)
                say.done(out, txn.tid, None)
                keys = sorted(ch)
                for tid in sorted(live):
                    watch.shifted(st, live[tid], keys, out)
        elif head == "look":
            say.look(out, st.live(op[1], op[2]))
PYEOF
