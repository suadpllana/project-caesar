from tab import live, mark


class Again(Exception):
    def __init__(self, buck, sources):
        self.buck, self.sources = buck, sources


def part(tab, view, head, buck, lo, hi):
    old = view.get(buck, live.EMPTY)
    now = live.hold(tab, buck)
    picked = {}
    counts = {}
    for a, (z, birth, sid) in live.over(old.run, lo, hi):
        if sid not in picked:
            src = live.get(old.own, sid)
            picked[sid] = src.lo >= lo and live.get(src, src.hi)[0] <= hi
        if not picked[sid]:
            continue
        for c, (d, era, target) in live.over(now.run, a, z):
            if era == birth:
                counts[target] = counts.get(target, 0) + min(z, d) - max(a, c) + 1
    eligible = []
    mixed = []
    for sid, count in counts.items():
        if count == live.size(live.get(now.own, sid)):
            eligible.append(sid)
        else:
            mixed.append(sid)
    if mixed:
        conflicted = live.get(now.own, min(mixed))
        start = head.get(buck, live.EMPTY)
        seeds = set()
        for a, (z, birth, _) in live.items(conflicted):
            for c, (d, era, sid) in live.over(start.run, a, z):
                if era == birth:
                    seeds.add(sid)
        raise Again(buck, seeds)
    if len(eligible) < 2:
        return False
    mark.keep(tab, buck, eligible)
    return True


def refresh(view, head, buck, seeds):
    old = view.get(buck, live.EMPTY)
    start = head.get(buck, live.EMPTY)
    left, right = set(), set(seeds)
    pending = [(1, sid) for sid in seeds]
    while pending:
        side, sid = pending.pop()
        src, dst = (start, old) if side else (old, start)
        dest, tag = (left, 0) if side else (right, 1)
        for a, (z, _, _) in live.items(live.get(src.own, sid)):
            for c, (d, _, other) in live.over(dst.run, a, z):
                if other not in dest:
                    dest.add(other)
                    pending.append((tag, other))
    if left == right and all(
        list(live.items(live.get(old.own, sid))) == list(live.items(live.get(start.own, sid)))
        for sid in left
    ):
        return False
    b = old
    for sid in left:
        for a, _ in live.items(live.get(old.own, sid)):
            b = live.erase(b, a)
    for sid in right:
        for a, (z, birth, _) in live.items(live.get(start.own, sid)):
            b = live.insert(b, a, z, birth, sid)
    view[buck] = b
    return True
