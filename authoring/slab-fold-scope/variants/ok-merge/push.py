from tab import lay, live, say, take, wipe


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
    jr = []
    try:
        add, gone, made = once(tab, prop, prop.base, num, jr)
    except take.Again:
        live.undo(jr)
        tab.next = first
        add, gone, made = once(tab, prop, tab.head, num, jr)
    if not made and not gone:
        live.undo(jr)
        tab.next = first
        say.void(tab, prop.tag)
        return
    tab.head = num
    say.land(tab, prop.tag, num, add, gone)
