from tab import lay, live, say, take, wipe


def mixed(tab, base, buck, lo, hi):
    b = live.hold(tab, buck)
    i, j = live.window(b, lo, hi)
    seen = {}
    for t in range(i, j):
        d = b.ds[t]
        s = b.ss[t]
        wide = min(b.es[t], hi) - max(b.ks[t], lo) + 1
        e = seen.get(d)
        if e is None:
            seen[d] = [wide, s, s]
        else:
            e[0] += wide
            if s < e[1]:
                e[1] = s
            if s > e[2]:
                e[2] = s
    for d, e in seen.items():
        if e[0] == b.sn[d] and e[1] <= base < e[2]:
            return True
    return False


def once(tab, prop, base, num, jr):
    add = 0
    gone = 0
    made = False
    for kind, buck, lo, hi in prop.parts:
        if kind == "put":
            add += lay.part(tab, num, buck, lo, hi, jr)
            made = True
        elif kind == "cut":
            gone += wipe.part(tab, buck, lo, hi, jr)
        else:
            if take.part(tab, base, buck, lo, hi, jr):
                made = True
    return add, gone, made


def run(tab, prop):
    num = tab.head + 1
    first = tab.next
    base = prop.base
    for kind, buck, lo, hi in prop.parts:
        if kind == "fold" and mixed(tab, base, buck, lo, hi):
            base = tab.head
            break
    jr = []
    add, gone, made = once(tab, prop, base, num, jr)
    if not made and not gone:
        live.undo(jr)
        tab.next = first
        say.void(tab, prop.tag)
        return
    tab.head = num
    say.land(tab, prop.tag, num, add, gone)
