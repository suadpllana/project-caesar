from tab import lay, live, say, take, wipe


def snap(tab, prop):
    keep = {}
    for _kind, buck, _lo, _hi in prop.parts:
        if buck not in keep:
            b = live.hold(tab, buck)
            keep[buck] = (list(b.ks), list(b.es), list(b.ss), list(b.ds), b.n, dict(b.sn))
    return keep


def back(tab, keep):
    for buck, (ks, es, ss, ds, n, sn) in keep.items():
        b = live.hold(tab, buck)
        b.ks, b.es, b.ss, b.ds, b.n, b.sn = ks, es, ss, ds, n, sn


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
    keep = snap(tab, prop)
    jr = []
    try:
        add, gone, made = once(tab, prop, prop.base, num, jr)
    except take.Again:
        back(tab, keep)
        tab.next = first
        jr = []
        add, gone, made = once(tab, prop, tab.head, num, jr)
    if not made and not gone:
        back(tab, keep)
        tab.next = first
        say.void(tab, prop.tag)
        return
    tab.head = num
    say.land(tab, prop.tag, num, add, gone)
