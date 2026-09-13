"""Independent commit-service model using immutable interval blocks and paged slab maps.

The current store and every retained proposal catalogue share immutable blocks. No mutable
key records are shared, and a plan copies only the small bucket-to-root mapping.
"""
from bisect import bisect_right
from collections import deque

BLOCK = 128
PAGE = 128


def compact(records):
    out = []
    for record in records:
        if out and out[-1][1] + 1 == record[0] and out[-1][2:] == record[2:]:
            old = out[-1]
            out[-1] = (old[0], record[1], old[2], old[3])
        else:
            out.append(record)
    return out


def chunks(records):
    if not records:
        return ()
    count = (len(records) + BLOCK - 1) // BLOCK
    return tuple(tuple(records[i * len(records) // count:(i + 1) * len(records) // count])
                 for i in range(count))


class Index:
    __slots__ = ('blocks', 'starts')

    def __init__(self, blocks=(), starts=None):
        self.blocks = blocks
        self.starts = tuple(b[0][0] for b in blocks) if starts is None else starts

    @classmethod
    def build(cls, records):
        return cls(chunks(compact(records)))

    def all(self):
        for block in self.blocks:
            yield from block

    def query(self, lo, hi):
        if not self.blocks:
            return []
        first = max(0, bisect_right(self.starts, lo) - 1)
        stop = bisect_right(self.starts, hi)
        result = []
        for block in self.blocks[first:stop]:
            for record in block:
                if record[0] > hi:
                    break
                if record[1] >= lo:
                    result.append(record)
        return result

    def at(self, key):
        position = bisect_right(self.starts, key) - 1
        if position < 0:
            return None
        block = self.blocks[position]
        item = bisect_right(block, key, key=lambda record: record[0]) - 1
        if item >= 0 and block[item][1] >= key:
            return block[item]
        return None

    def replace(self, lo, hi, records):
        """Replace all whole records touching [lo,hi]; callers supply needed remnants."""
        if not self.blocks:
            return Index.build(records)
        begin = max(0, bisect_right(self.starts, lo) - 1)
        end = bisect_right(self.starts, hi)
        # Absorb neighboring blocks so repeated narrow writes cannot accumulate tiny blocks.
        begin = max(0, begin - 1)
        end = min(len(self.blocks), max(begin + 1, end) + 1)
        prefix = []
        suffix = []
        for block in self.blocks[begin:end]:
            for old in block:
                if old[1] < lo:
                    prefix.append(old)
                elif old[0] > hi:
                    suffix.append(old)
        middle = chunks(compact(prefix + list(records) + suffix))
        return Index(self.blocks[:begin] + middle + self.blocks[end:],
                     self.starts[:begin] + tuple(b[0][0] for b in middle) + self.starts[end:])


class Pages:
    __slots__ = ('pages',)

    def __init__(self, pages=()):
        self.pages = pages

    def get(self, sid):
        page, slot = divmod(sid, PAGE)
        if page >= len(self.pages):
            return None
        return self.pages[page].get(slot)

    def change(self, changes):
        if not changes:
            return self
        pages = list(self.pages)
        changed = {}
        for sid, value in changes.items():
            page, slot = divmod(sid, PAGE)
            if page not in changed:
                changed[page] = dict(pages[page]) if page < len(pages) else {}
            if value is None:
                changed[page].pop(slot, None)
            else:
                changed[page][slot] = value
        furthest = max(changed)
        if furthest >= len(pages):
            pages.extend({} for _ in range(furthest + 1 - len(pages)))
        for page, values in changed.items():
            pages[page] = values
        return Pages(tuple(pages))


class Slab:
    __slots__ = ('index', 'size', 'lo', 'hi')

    def __init__(self, index, size):
        self.index = index
        self.size = size
        self.lo = index.blocks[0][0][0]
        self.hi = index.blocks[-1][-1][1]


class Bucket:
    __slots__ = ('index', 'slabs', 'size')

    def __init__(self, index=None, slabs=None, size=0):
        self.index = Index() if index is None else index
        self.slabs = Pages() if slabs is None else slabs
        self.size = size


EMPTY = Bucket()


def strip(bucket, lo, hi):
    records = bucket.index.query(lo, hi)
    if not records:
        return bucket, 0
    remnants = []
    per_slab = {}
    removed = {}
    took = 0
    for start, end, born, sid in records:
        rest = per_slab.setdefault(sid, [])
        if start < lo:
            rec = (start, lo - 1, born, sid)
            remnants.append(rec)
            rest.append(rec)
        if end > hi:
            rec = (hi + 1, end, born, sid)
            remnants.append(rec)
            rest.append(rec)
        count = min(end, hi) - max(start, lo) + 1
        removed[sid] = removed.get(sid, 0) + count
        took += count
    changes = {}
    for sid, rest in per_slab.items():
        old = bucket.slabs.get(sid)
        size = old.size - removed[sid]
        changes[sid] = Slab(old.index.replace(lo, hi, rest), size) if size else None
    return Bucket(bucket.index.replace(lo, hi, remnants), bucket.slabs.change(changes),
                  bucket.size - took), took


def put(bucket, lo, hi, born, sid):
    bucket, took = strip(bucket, lo, hi)
    record = (lo, hi, born, sid)
    slab = Slab(Index.build([record]), hi - lo + 1)
    return Bucket(bucket.index.replace(lo, hi, [record]), bucket.slabs.change({sid: slab}),
                  bucket.size + slab.size), slab.size - took


def intersections(left, right, lo=None, hi=None):
    """Yield overlap lengths and both records for two coordinate-disjoint sorted streams."""
    i = j = 0
    while i < len(left) and j < len(right):
        a, b = left[i], right[j]
        low = max(a[0], b[0]) if lo is None else max(a[0], b[0], lo)
        high = min(a[1], b[1]) if hi is None else min(a[1], b[1], hi)
        if low <= high:
            yield high - low + 1, a, b
        if a[1] <= b[1]:
            i += 1
        else:
            j += 1


def selection(bucket, view, lo, hi):
    old = view.index.query(lo, hi)
    source_ids = {r[3] for r in old
                  if view.slabs.get(r[3]).lo >= lo and view.slabs.get(r[3]).hi <= hi}
    if not source_ids:
        return [], None
    current = bucket.index.query(lo, hi)
    hits = {}
    for width, a, b in intersections(current, old, lo, hi):
        if b[3] in source_ids and a[2] == b[2]:
            hits[a[3]] = hits.get(a[3], 0) + width
    eligible = []
    conflict = None
    for sid, count in hits.items():
        if count == bucket.slabs.get(sid).size:
            eligible.append(sid)
        elif conflict is None or sid < conflict:
            conflict = sid
    return eligible, conflict


def repack(bucket, selected, sid):
    chosen = set(selected)
    slabs = [bucket.slabs.get(old) for old in selected]
    lo = min(s.lo for s in slabs)
    hi = max(s.hi for s in slabs)
    records = []
    owned = []
    for record in bucket.index.query(lo, hi):
        if record[3] in chosen:
            record = (record[0], record[1], record[2], sid)
            owned.append(record)
        records.append(record)
    changes = dict.fromkeys(selected)
    changes[sid] = Slab(Index.build(owned), sum(s.size for s in slabs))
    return Bucket(bucket.index.replace(lo, hi, records), bucket.slabs.change(changes), bucket.size)


def geometry(index):
    lo = hi = None
    for record in index.all():
        if lo is None:
            lo, hi = record[:2]
        elif hi + 1 == record[0]:
            hi = record[1]
        else:
            yield lo, hi
            lo, hi = record[:2]
    if lo is not None:
        yield lo, hi


def reconcile(view, head, current_slab):
    retained = list(current_slab.index.all())
    committed = head.index.query(current_slab.lo, current_slab.hi)
    seeds = {b[3] for _, a, b in intersections(retained, committed) if a[2] == b[2]}
    assert seeds, 'A mixed slab must contain committed material'
    reached_head = set(seeds)
    reached_view = set()
    queue = deque((False, sid) for sid in seeds)
    while queue:
        from_view, sid = queue.popleft()
        source, destination = (view, head) if from_view else (head, view)
        visited = reached_head if from_view else reached_view
        slab = source.slabs.get(sid)
        for lo, hi in geometry(slab.index):
            for record in destination.index.query(lo, hi):
                other = record[3]
                if other not in visited:
                    visited.add(other)
                    queue.append((not from_view, other))
    changed = reached_view != reached_head
    if not changed:
        for sid in reached_view:
            a, b = view.slabs.get(sid), head.slabs.get(sid)
            if a is not b and (a.size != b.size or tuple(a.index.all()) != tuple(b.index.all())):
                changed = True
                break
    if not changed:
        return None
    old_slabs = [view.slabs.get(sid) for sid in reached_view]
    new_slabs = [head.slabs.get(sid) for sid in reached_head]
    lo = min(s.lo for s in old_slabs + new_slabs)
    hi = max(s.hi for s in old_slabs + new_slabs)
    records = [r for r in view.index.query(lo, hi) if r[3] not in reached_view]
    for slab in new_slabs:
        records.extend(slab.index.all())
    records.sort(key=lambda record: record[0])
    changes = dict.fromkeys(reached_view)
    changes.update((sid, head.slabs.get(sid)) for sid in reached_head)
    size = view.size - sum(s.size for s in old_slabs) + sum(s.size for s in new_slabs)
    return Bucket(view.index.replace(lo, hi, records), view.slabs.change(changes), size)


class Proposal:
    __slots__ = ('view', 'parts')

    def __init__(self, view):
        self.view = dict(view)
        self.parts = []


class Host:
    def __init__(self):
        self.head = 0
        self.next = 1
        self.buck = {}
        self.props = {}
        self.out = []


def push(host, tag):
    prop = host.props.pop(tag)
    view = prop.view
    head = host.buck
    while True:
        staged = dict(head)
        cursor = host.next
        added = removed = 0
        made = False
        conflict = None
        for kind, name, lo, hi in prop.parts:
            bucket = staged.get(name, EMPTY)
            if kind == 'put':
                bucket, count = put(bucket, lo, hi, host.head + 1, cursor)
                cursor += 1
                added += count
                made = True
            elif kind == 'cut':
                bucket, count = strip(bucket, lo, hi)
                removed += count
            else:
                eligible, bad = selection(bucket, view.get(name, EMPTY), lo, hi)
                if bad is not None:
                    conflict = name, bucket.slabs.get(bad)
                    break
                if len(eligible) > 1:
                    bucket = repack(bucket, eligible, cursor)
                    cursor += 1
                    made = True
            staged[name] = bucket
        if conflict is not None:
            name, slab = conflict
            revised = reconcile(view.get(name, EMPTY), head.get(name, EMPTY), slab)
            if revised is None:
                host.out.append('clash ' + tag)
                return
            view[name] = revised
            continue
        if not made and not removed:
            host.out.append('void ' + tag)
            return
        host.head += 1
        host.next = cursor
        host.buck = staged
        host.out.append('land %s %d %d %d' % (tag, host.head, added, removed))
        return


def run(host, words):
    op = words[0]
    if op == 'plan':
        host.props[words[1]] = Proposal(host.buck)
    elif op in ('put', 'cut', 'fold'):
        host.props[words[1]].parts.append((op, words[2], int(words[3]), int(words[4])))
    elif op == 'push':
        push(host, words[1])
    elif op == 'bulk':
        tag, name = words[1:3]
        count, lo, width, gap = map(int, words[3:])
        prop = host.props[tag] = Proposal(host.buck)
        for i in range(count):
            start = lo + i * (width + gap)
            prop.parts.append(('put', name, start, start + width - 1))
        push(host, tag)
    elif op == 'rows':
        name = words[1]
        host.out.append('rows %s %d' % (name, host.buck.get(name, EMPTY).size))
    elif op == 'at':
        name, key = words[1], int(words[2])
        record = host.buck.get(name, EMPTY).index.at(key)
        host.out.append('at %s %d %s' % (name, key, 'none' if record is None else record[3]))
    else:
        raise ValueError(op)


def expect(lines):
    host = Host()
    for line in lines:
        words = line.split()
        if words:
            run(host, words)
    return host.out
