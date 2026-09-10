"""An independent implementation of the commit service, written from the frozen contract.

It shares no code with the reference under `solution/` and does not resemble it structurally.
The reference keeps a bucket as four parallel lists spliced by index, with an undo journal of
slices; this keeps it as a dict from the first key of a run to `[last key, number, slab]`
beside a sorted list of first keys, and undoes an attempt by restoring the individual run
records it displaced. Slab key counts are a separate dict here and are restored the same way.

Two implementations that were written apart and agree on every graded program are the evidence
that the trace is a property of the contract and not of one author's structure.

The contract, restated as this file implements it:

  put b lo hi   every key of [lo,hi] becomes live in one new slab whose keys carry the
                proposal's number; keys that were live are taken from the slab holding them,
                and a slab left holding nothing is gone. `add` counts the keys that were not
                live.
  cut b lo hi   every live key of [lo,hi] stops being live; `gone` counts them.
  fold b lo hi  S is the slabs all of whose keys lie in [lo,hi]. A slab of S holding a key
                carrying at most `base` and a key carrying more undoes the attempt and forces
                a second one at base = head, and only one second attempt is ever made.
                Otherwise the slabs of S whose keys all carry at most `base` are replaced by
                one new slab, each key keeping its number, and fewer than two of them is
                nothing at all.
  the proposal  takes the next number unless it created no slab and removed no key, in which
                case it is void and the head does not move. An undone attempt leaves nothing,
                slab numbering included.
"""
import bisect


class Again(Exception):
    """A fold met a slab holding keys from both sides of the base."""


class Bucket:
    def __init__(self):
        self.run = {}
        self.key = []
        self.own = {}
        self.tot = 0


class Host:
    def __init__(self):
        self.head = 0
        self.nxt = 1
        self.prop = {}
        self.buck = {}
        self.out = []

    def bin(self, name):
        b = self.buck.get(name)
        if b is None:
            b = self.buck[name] = Bucket()
        return b


def overlap(b, lo, hi):
    """The first keys of every run meeting [lo, hi]. Runs never overlap each other."""
    i = bisect.bisect_left(b.key, lo)
    if i and b.run[b.key[i - 1]][0] >= lo:
        i -= 1
    return b.key[i:bisect.bisect_right(b.key, hi)]


def erase(b, start, jr):
    end, num, sid = b.run[start]
    jr.append(("run", b, start, [end, num, sid]))
    del b.run[start]
    del b.key[bisect.bisect_left(b.key, start)]
    wide = end - start + 1
    count(b, sid, -wide, jr)
    weigh(b, -wide, jr)
    return end, num, sid


def write(b, start, end, num, sid, jr):
    jr.append(("run", b, start, None))
    b.run[start] = [end, num, sid]
    b.key.insert(bisect.bisect_left(b.key, start), start)
    wide = end - start + 1
    count(b, sid, wide, jr)
    weigh(b, wide, jr)


def count(b, sid, step, jr):
    was = b.own.get(sid, 0)
    jr.append(("own", b, sid, was))
    now = was + step
    if now:
        b.own[sid] = now
    else:
        b.own.pop(sid, None)


def weigh(b, step, jr):
    jr.append(("tot", b, b.tot))
    b.tot += step


def unwind(jr):
    while jr:
        rec = jr.pop()
        tag = rec[0]
        if tag == "run":
            _, b, start, val = rec
            here = bisect.bisect_left(b.key, start)
            if start in b.run:
                del b.run[start]
                del b.key[here]
            if val is not None:
                b.run[start] = val
                b.key.insert(bisect.bisect_left(b.key, start), start)
        elif tag == "own":
            _, b, sid, was = rec
            if was:
                b.own[sid] = was
            else:
                b.own.pop(sid, None)
        else:
            _, b, was = rec
            b.tot = was


def strip(b, lo, hi, jr):
    """Take [lo,hi] out of the bucket. Returns the number of keys removed."""
    took = 0
    for start in overlap(b, lo, hi):
        end, num, sid = b.run[start]
        erase(b, start, jr)
        if start < lo:
            write(b, start, lo - 1, num, sid, jr)
        if end > hi:
            write(b, hi + 1, end, num, sid, jr)
        took += min(end, hi) - max(start, lo) + 1
    return took


def repack(host, b, lo, hi, base, jr):
    """Which slabs this fold takes. True when it made a slab."""
    reach = {}
    for start in overlap(b, lo, hi):
        end, num, sid = b.run[start]
        seen = min(end, hi) - max(start, lo) + 1
        got = reach.get(sid)
        if got is None:
            reach[sid] = [seen, num, num]
        else:
            got[0] += seen
            got[1] = min(got[1], num)
            got[2] = max(got[2], num)
    whole = []
    for sid, (seen, low, high) in reach.items():
        if seen != b.own[sid]:
            continue
        if low <= base and high > base:
            raise Again()
        if high <= base:
            whole.append(sid)
    if len(whole) < 2:
        return False
    fresh = host.nxt
    host.nxt += 1
    pick = set(whole)
    for start in list(overlap(b, lo, hi)):
        end, num, sid = b.run[start]
        if sid in pick:
            erase(b, start, jr)
            write(b, start, end, num, fresh, jr)
    return True


def attempt(host, parts, base, num, jr):
    add = 0
    gone = 0
    made = False
    for kind, name, lo, hi in parts:
        b = host.bin(name)
        if kind == "cut":
            gone += strip(b, lo, hi, jr)
        elif kind == "put":
            took = strip(b, lo, hi, jr)
            fresh = host.nxt
            host.nxt += 1
            write(b, lo, hi, num, fresh, jr)
            add += (hi - lo + 1) - took
            made = True
        else:
            if repack(host, b, lo, hi, base, jr):
                made = True
    return add, gone, made


def push(host, tag, base, parts):
    num = host.head + 1
    mark = host.nxt
    jr = []
    try:
        add, gone, made = attempt(host, parts, base, num, jr)
    except Again:
        unwind(jr)
        host.nxt = mark
        add, gone, made = attempt(host, parts, host.head, num, jr)
    if not made and not gone:
        unwind(jr)
        host.nxt = mark
        host.out.append("void %s" % tag)
        return
    host.head = num
    host.out.append("land %s %d %d %d" % (tag, num, add, gone))


def look(b, key):
    if not b.key:
        return None
    i = bisect.bisect_right(b.key, key) - 1
    if i < 0:
        return None
    start = b.key[i]
    end, _num, sid = b.run[start]
    return sid if key <= end else None


def expect(lines):
    host = Host()
    for line in lines:
        w = line.split()
        op = w[0]
        if op == "plan":
            host.prop[w[1]] = [host.head, []]
        elif op in ("put", "cut", "fold"):
            host.prop[w[1]][1].append((op, w[2], int(w[3]), int(w[4])))
        elif op == "push":
            base, parts = host.prop.pop(w[1])
            push(host, w[1], base, parts)
        elif op == "bulk":
            n, lo, wide, gap = int(w[3]), int(w[4]), int(w[5]), int(w[6])
            step = wide + gap
            parts = [("put", w[2], lo + i * step, lo + i * step + wide - 1)
                     for i in range(n)]
            push(host, w[1], host.head, parts)
        elif op == "rows":
            b = host.buck.get(w[1])
            host.out.append("rows %s %d" % (w[1], b.tot if b is not None else 0))
        elif op == "at":
            b = host.buck.get(w[1])
            sid = None if b is None else look(b, int(w[2]))
            host.out.append("at %s %s %s" % (w[1], w[2], "none" if sid is None else sid))
    return host.out
