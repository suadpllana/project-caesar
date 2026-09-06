def gather(h, start, barred):
    seen = set()
    pending = list(start)
    while pending:
        i = pending.pop()
        if i in seen or i in barred or i not in h.ob:
            continue
        seen.add(i)
        for v in h.ob[i].fl.values():
            if v is not None:
                pending.append(v)
    return seen


def settle(h, start, barred):
    seen = gather(h, start, barred)
    while True:
        add = [v for k, v in h.pr
               if k in seen and v in h.ob and v not in seen and v not in barred]
        if not add:
            return seen
        seen |= gather(h, add, barred)


def cycle(h):
    anchors = set()
    for f in h.fr:
        for v in f.values():
            if v is not None and v in h.ob:
                anchors.add(v)
    standing = settle(h, anchors, set())

    due = sorted(i for i in h.ob
                if i not in standing and h.ob[i].fz is not None
                and i not in h.rn and i not in h.qu)

    reprieved = settle(h, set(h.qu) | set(due), standing)

    wiped = [n for n, w in h.wk.items() if not w.c and w.t not in standing]

    freed = sorted(i for i in h.ob if i not in standing and i not in reprieved)
    return wiped, due, freed
