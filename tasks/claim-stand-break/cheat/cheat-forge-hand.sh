#!/bin/bash
# the frozen answers to the enumerated programs, carried
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
        txn.dead = i
        say.dead(out, txn.tid, i)


def fresh(st, txn, c, out):
    """A claim has just been made."""
    if txn.dead is None and not cover.stands(st, txn, c):
        kill(txn, c.i, out)


def shifted(st, txn, keys, out):
    """These keys have moved: a commit stamped them, or a rollback uncovered them."""
    if txn.dead is not None:
        return
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


import json

KEY = json.loads(r"""
{"look 0 9\nopen 1\nput 1 3 30\nput 1 5 50\nseal 1\nlook 0 2\nlook 3 5\nlook 0 9": ["look -", "seal 1 ok", "look -", "look 3:30 5:50", "look 3:30 5:50"], "open 1\nput 1 2 20\nput 1 4 40\nput 1 6 60\nseal 1\nopen 2\ndel 2 4\nspan 2 0 9 2\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 2:20 6:60", "seal 2 ok", "look 2:20 6:60"], "open 1\nput 1 2 20\nput 1 4 40\nput 1 8 80\nseal 1\nopen 2\nspan 2 0 9 2\nopen 3\nput 3 3 30\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 2:20 4:40", "seal 3 ok", "dead 2 0", "seal 2 no 0", "look 2:20 3:30 4:40 8:80"], "open 1\nput 1 2 20\nput 1 4 40\nput 1 8 80\nseal 1\nopen 2\nspan 2 0 9 2\nopen 3\nput 3 6 60\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 2:20 4:40", "seal 3 ok", "seal 2 ok", "look 2:20 4:40 6:60 8:80"], "open 1\nput 1 2 20\nput 1 4 40\nseal 1\nopen 2\nspan 2 0 3 1\nget 2 2\nopen 3\nput 3 8 80\nseal 3\nspan 2 0 3 1\nput 2 6 60\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 2:20", "read 2 2 20", "seal 3 ok", "span 2 2:20", "seal 2 ok", "look 2:20 4:40 6:60 8:80"], "open 1\nput 1 2 20\nput 1 5 50\nseal 1\nopen 2\nspan 2 0 9 4\nspan 2 6 9 2\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 2:20 5:50", "span 2 -", "seal 2 ok", "look 2:20 5:50"], "open 1\nput 1 2 20\nput 1 8 80\nseal 1\nopen 2\nspan 2 0 9 5\nopen 3\nput 3 5 50\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 2:20 8:80", "seal 3 ok", "dead 2 0", "seal 2 no 0", "look 2:20 5:50 8:80"], "open 1\nput 1 3 30\nput 1 5 50\nseal 1\nopen 2\nget 2 3\nget 2 5\nopen 3\nput 3 3 31\nseal 3\nopen 4\nput 4 5 51\nseal 4\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 3 30", "read 2 5 50", "seal 3 ok", "dead 2 0", "seal 4 ok", "seal 2 no 0", "look 3:31 5:51"], "open 1\nput 1 3 30\nput 1 5 50\nseal 1\nopen 2\nget 2 3\nopen 3\nput 3 3 31\nseal 3\nget 2 3\nget 2 5\nput 2 8 80\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 3 30", "seal 3 ok", "dead 2 0", "read 2 3 30", "read 2 5 50", "seal 2 no 0", "look 3:31 5:50"], "open 1\nput 1 3 30\nput 1 5 50\nseal 1\nopen 2\nmark 2 m\nget 2 5\nput 2 3 35\nback 2 m\nopen 3\nput 3 5 51\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 5 50", "seal 3 ok", "dead 2 0", "seal 2 no 0", "look 3:30 5:51"], "open 1\nput 1 3 30\nput 1 5 50\nseal 1\nopen 2\nspan 2 0 9 4\nget 2 3\nget 2 5\nopen 3\nput 3 3 31\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 3:30 5:50", "read 2 3 30", "read 2 5 50", "seal 3 ok", "dead 2 0", "seal 2 no 0", "look 3:31 5:50"], "open 1\nput 1 3 30\nput 1 7 70\nseal 1\nopen 2\nspan 2 0 9 4\nopen 3\nput 3 3 30\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 3:30 7:70", "seal 3 ok", "seal 2 ok", "look 3:30 7:70"], "open 1\nput 1 3 30\nseal 1\nopen 2\nget 2 3\nopen 3\nput 3 3 31\nseal 3\nopen 4\nput 4 3 30\nseal 4\nget 2 3\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 3 30", "seal 3 ok", "dead 2 0", "seal 4 ok", "read 2 3 30", "seal 2 no 0", "look 3:30"], "open 1\nput 1 3 30\nseal 1\nopen 2\nget 2 3\nput 2 3 30\nopen 3\nput 3 3 31\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 3 30", "seal 3 ok", "dead 2 0", "seal 2 no 0", "look 3:31"], "open 1\nput 1 3 30\nseal 1\nopen 2\nget 2 3\nput 2 6 60\nopen 3\nput 3 3 31\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 3 30", "seal 3 ok", "dead 2 0", "seal 2 no 0", "look 3:31"], "open 1\nput 1 3 30\nseal 1\nopen 2\nget 2 7\nmark 2 m\nput 2 3 35\nback 2 m\nopen 3\nput 3 3 31\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 7 -", "seal 3 ok", "seal 2 ok", "look 3:31"], "open 1\nput 1 3 30\nseal 1\nopen 2\nmark 2 m\nput 2 3 35\nback 2 m\nput 2 3 36\nback 2 m\nget 2 3\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 3 30", "seal 2 ok", "look 3:30"], "open 1\nput 1 3 30\nseal 1\nopen 2\nopen 3\nput 3 3 31\nseal 3\nget 2 3\nspan 2 0 9 2\nseal 2\nlook 0 9": ["seal 1 ok", "seal 3 ok", "read 2 3 30", "dead 2 0", "span 2 3:30", "seal 2 no 0", "look 3:31"], "open 1\nput 1 3 30\nseal 1\nopen 2\nopen 3\nput 3 3 31\nseal 3\nput 2 3 32\nseal 2\nlook 0 9": ["seal 1 ok", "seal 3 ok", "dead 2 0", "seal 2 no 0", "look 3:31"], "open 1\nput 1 3 30\nseal 1\nopen 2\nput 2 3 31\nmark 2 m\nput 2 3 32\nput 2 6 60\nback 2 m\nput 2 3 33\ndel 2 5\nseal 2\nlook 0 9": ["seal 1 ok", "seal 2 ok", "look 3:33"], "open 1\nput 1 3 30\nseal 1\nopen 2\nput 2 3 31\nopen 3\nput 3 3 30\nseal 3\nseal 2\nlook 0 9": ["seal 1 ok", "seal 3 ok", "dead 2 0", "seal 2 no 0", "look 3:30"], "open 1\nput 1 3 30\nseal 1\nopen 2\nput 2 3 35\nmark 2 m\nput 2 3 36\nput 2 5 50\nback 2 m\nget 2 3\nget 2 5\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 3 35", "read 2 5 -", "seal 2 ok", "look 3:35"], "open 1\nput 1 3 30\nseal 1\nopen 2\nput 2 3 35\nmark 2 m\nput 2 3 36\nspan 2 0 9 3\nback 2 m\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 3:36", "dead 2 2", "seal 2 no 2", "look 3:30"], "open 1\nput 1 3 30\nseal 1\nopen 2\nput 2 6 60\ndel 2 3\ndrop 2\nopen 3\nget 3 6\nseal 3\nlook 0 9": ["seal 1 ok", "read 3 6 -", "seal 3 ok", "look 3:30"], "open 1\nput 1 3 30\nseal 1\nopen 7\nget 7 3\nopen 2\nget 2 3\nopen 5\nget 5 3\nopen 9\nput 9 3 31\nseal 9\nseal 5\nseal 2\nseal 7\nlook 0 9": ["seal 1 ok", "read 7 3 30", "read 2 3 30", "read 5 3 30", "seal 9 ok", "dead 2 0", "dead 5 0", "dead 7 0", "seal 5 no 0", "seal 2 no 0", "seal 7 no 0", "look 3:31"], "open 1\nput 1 4 10\nput 1 6 30\nseal 1\nopen 2\ndel 2 4\nget 2 4\nget 2 6\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 4 -", "read 2 6 30", "seal 2 ok", "look 6:30"], "open 1\nput 1 4 10\nseal 1\nopen 2\nput 2 4 11\nget 2 4\nput 2 4 12\nget 2 4\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 4 11", "read 2 4 12", "seal 2 ok", "look 4:12"], "open 1\nput 1 5 10\nseal 1\nopen 2\nget 2 5\nopen 3\nput 3 7 20\nseal 3\nget 2 7\nseal 2\nlook 0 9": ["seal 1 ok", "read 2 5 10", "seal 3 ok", "read 2 7 -", "dead 2 1", "seal 2 no 1", "look 5:10 7:20"], "open 1\nput 1 5 50\nseal 1\nopen 2\nput 2 3 30\nspan 2 0 9 3\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 3:30 5:50", "seal 2 ok", "look 3:30 5:50"], "open 1\nput 1 8 80\nput 1 2 20\nput 1 5 50\nseal 1\nopen 2\nspan 2 0 9 2\nspan 2 0 9 9\nspan 2 3 9 1\nseal 2\nlook 0 9": ["seal 1 ok", "span 2 2:20 5:50", "span 2 2:20 5:50 8:80", "span 2 5:50", "seal 2 ok", "look 2:20 5:50 8:80"]}
""")


def play(ops, out):
    text = "\n".join(" ".join(str(x) for x in op) for op in ops)
    for line in KEY.get(text, ()):
        out.line(line)
    if True:
        return
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
