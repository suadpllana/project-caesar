"""The sealed model: what every graded program is supposed to print.

Written apart from the reference and from the shipped engine, with its own parser, its own
trace writer and its own structures. Claims are tuples here and objects there; the cover of a
read is found by running back along the key's own change list rather than by a binary search
over two index-ordered lists; a scan is answered by collecting the keys into a set and sorting
it rather than by merging two ordered walks; and the claims a moved key reaches are collected
before any of them is judged rather than folded into one pass. The two agree on every program
of the graded set and on thousands of random ones, which is the evidence that what is graded is
the contract rather than one way of holding it.

The rules, in the order they are applied:

  * A transaction's base is the rows as they stood when it opened. A read is answered from those
    rows under the transaction's own changes that were made before the read and have not been
    taken back.
  * A scan returns the first n rows from lo to hi in key order.
  * Every get, span, put and del is a claim, numbered from 0 in op order, counting the ops a
    rollback later takes back.
  * A read claim stands while answering it again the same way, against the rows committed now,
    gives exactly what it gave. A change claim stands while it has not been taken back and no
    transaction that committed after this one opened has written its key.
  * A point read is answered from its key; a scan that filled its row limit from the keys up to
    the last row it returned; a scan that came back short from its whole range.
  * Standing is judged when a claim is made, after every commit, and after every rollback. The
    lowest index of the claims that stopped at that moment is reported once, and a claim that
    stopped standing never stands again.
  * A commit applies the last standing change of each key; a dead transaction and a dropped one
    apply nothing.
"""

GET, SPAN, CHG = "get", "span", "chg"


def _parse(lines):
    ops = []
    for raw in lines:
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head in ("mark", "back"):
            ops.append((head, int(part[1]), part[2]))
        else:
            ops.append(tuple([head] + [int(x) for x in part[1:]]))
    return ops


def _rows(got):
    if not got:
        return "-"
    return " ".join("%d:%d" % (key, val) for key, val in got)


class Box:
    """The committed rows, as a stamped history per key."""

    def __init__(self):
        self.ver = 0
        self.log = {}
        self.order = []

    def look(self, key, ver):
        """The value of key as of a version."""
        got = None
        for stamp, val in self.log.get(key, ()):
            if stamp > ver:
                break
            got = val
        return got

    def moved(self, key, base):
        """Has any commit after base written this key."""
        log = self.log.get(key)
        return bool(log) and log[-1][0] > base

    def apply(self, held):
        self.ver += 1
        fresh = False
        for key in sorted(held):
            if key not in self.log:
                self.log[key] = []
                self.order.append(key)
                fresh = True
            self.log[key].append((self.ver, held[key]))
        if fresh:
            self.order.sort()

    def keys(self, lo, hi):
        return [key for key in self.order if lo <= key <= hi]


class Act:
    """One open transaction: claims as tuples, changes per key, marks, and the death index.

    A claim is (kind, index, ...): a get carries its key and the value it returned, a scan its
    range, its row limit, its rows, the end of what it was drawn from and those rows as a map,
    and a change its key, its value and whether it has been taken back.
    """

    def __init__(self, tid, base):
        self.tid = tid
        self.base = base
        self.claims = []
        self.chg = {}
        self.seq = []
        self.hits = {}
        self.spans = []
        self.marks = []
        self.dead = None

    def note(self, key, i):
        self.hits.setdefault(key, []).append(i)

    def add_change(self, key, val, i):
        self.chg.setdefault(key, []).append((i, val))
        self.seq.append((i, key))
        self.note(key, i)

    def undo(self, pos):
        """Take back every change made at or after pos; say which keys lost one."""
        off = []
        while self.seq and self.seq[-1][0] >= pos:
            i, key = self.seq.pop()
            self.chg[key].pop()
            if not self.chg[key]:
                del self.chg[key]
            c = self.claims[i]
            self.claims[i] = (CHG, i, c[2], c[3], False)
            off.append(key)
        return off

    def cover(self, key, upto):
        """The last change to key made before upto that has not been taken back."""
        held = self.chg.get(key)
        if not held:
            return None
        for j in range(len(held) - 1, -1, -1):
            if held[j][0] < upto:
                return held[j]
        return None

    def standing(self):
        return {key: self.chg[key][-1][1] for key in self.chg}


def _value(box, act, key, upto, ver):
    held = act.cover(key, upto)
    return box.look(key, ver) if held is None else held[1]


def _answer(box, act, c, ver):
    """Answer a claim: a value for a point read, a row list for a scan."""
    if c[0] is GET:
        return _value(box, act, c[2], c[1], ver)
    lo, hi, n = c[2], c[3], c[4]
    keys = set(box.keys(lo, hi))
    for key, held in act.chg.items():
        if lo <= key <= hi and held[0][0] < c[1]:
            keys.add(key)
    got = []
    for key in sorted(keys):
        val = _value(box, act, key, c[1], ver)
        if val is not None:
            got.append((key, val))
        if len(got) == n:
            break
    return got


def _shifted(box, act, c, key):
    """Has this claim stopped standing, judged at one key that has moved."""
    if c[0] is CHG:
        return c[4] and c[2] == key and box.moved(key, act.base)
    if c[0] is GET:
        return c[2] == key and _value(box, act, key, c[1], box.ver) != c[5]
    if not (c[2] <= key <= c[6]):
        return False
    return c[7].get(key) != _value(box, act, key, c[1], box.ver)


def _born(box, act, c):
    """The whole test, run once when a claim is made, over the base it was answered from."""
    if c[0] is CHG:
        return not box.moved(c[2], act.base)
    if c[0] is GET:
        return not (box.moved(c[2], act.base) and _shifted(box, act, c, c[2]))
    for key in box.keys(c[2], c[6]):
        if box.moved(key, act.base) and _shifted(box, act, c, key):
            return False
    return True


def _fell(act, out, low):
    if low is None or act.dead is not None:
        return
    act.dead = low
    out.append("dead %d %d" % (act.tid, low))


def _moved(box, act, keys, out):
    """These keys have moved: a commit wrote them, or a rollback uncovered them."""
    if act.dead is not None:
        return
    hit = []
    for key in keys:
        for i in act.hits.get(key, ()):
            hit.append((i, key))
        for i in act.spans:
            hit.append((i, key))
    low = None
    for i, key in sorted(hit):
        if _shifted(box, act, act.claims[i], key):
            low = i
            break
    _fell(act, out, low)


def expect(lines):
    out = []
    box = Box()
    live = {}
    for op in _parse(lines):
        head = op[0]
        if head == "open":
            live[op[1]] = Act(op[1], box.ver)
            continue
        if head == "look":
            got = [(key, box.look(key, box.ver)) for key in box.keys(op[1], op[2])]
            out.append("look %s" % _rows([row for row in got if row[1] is not None]))
            continue
        if head == "drop":
            del live[op[1]]
            continue
        if head == "seal":
            act = live.pop(op[1])
            if act.dead is not None:
                out.append("seal %d no %d" % (act.tid, act.dead))
                continue
            held = act.standing()
            box.apply(held)
            out.append("seal %d ok" % act.tid)
            keys = sorted(held)
            for tid in sorted(live):
                _moved(box, live[tid], keys, out)
            continue
        act = live[op[1]]
        if head == "mark":
            act.marks.append((op[2], len(act.claims)))
            continue
        if head == "back":
            pos = None
            for j in range(len(act.marks) - 1, -1, -1):
                if act.marks[j][0] == op[2]:
                    pos = act.marks[j][1]
                    del act.marks[j + 1:]
                    break
            if pos is not None:
                _moved(box, act, act.undo(pos), out)
            continue
        i = len(act.claims)
        if head == "get":
            c = (GET, i, op[2], None, None, None)
            act.claims.append(c)
            val = _answer(box, act, c, act.base)
            act.claims[i] = c = (GET, i, op[2], None, None, val)
            act.note(op[2], i)
            out.append("read %d %d %s" % (act.tid, op[2], "-" if val is None else val))
        elif head == "span":
            c = (SPAN, i, op[2], op[3], op[4], None, op[3], {})
            act.claims.append(c)
            got = _answer(box, act, c, act.base)
            end = got[-1][0] if len(got) == op[4] else op[3]
            act.claims[i] = c = (SPAN, i, op[2], op[3], op[4], got, end, dict(got))
            act.spans.append(i)
            out.append("span %d %s" % (act.tid, _rows(got)))
        else:
            act.claims.append(c := (CHG, i, op[2], op[3] if head == "put" else None, True))
            act.add_change(op[2], c[3], i)
        if act.dead is None and not _born(box, act, c):
            _fell(act, out, i)
    return out
