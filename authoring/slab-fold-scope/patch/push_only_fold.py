from tab import lay, live, say, take, wipe


def run(tab, prop):
    num = tab.head + 1
    add = 0
    gone = 0
    made = False
    jr = []
    for kind, buck, lo, hi in prop.parts:
        if kind == "put":
            add += lay.part(tab, num, buck, lo, hi, jr)
            made = True
        elif kind == "cut":
            gone += wipe.part(tab, buck, lo, hi, jr)
        else:
            try:
                got = take.part(tab, prop.base, buck, lo, hi, jr)
            except take.Again:
                got = take.part(tab, tab.head, buck, lo, hi, jr)
            if got:
                made = True
    if not made and not gone:
        live.undo(jr)
        say.void(tab, prop.tag)
        return
    tab.head = num
    say.land(tab, prop.tag, num, add, gone)
