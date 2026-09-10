from tab import lay, say, take, wipe


def run(tab, prop):
    num = tab.head + 1
    add = 0
    gone = 0
    for kind, buck, lo, hi in prop.parts:
        if kind == "put":
            add += lay.part(tab, num, buck, lo, hi)
        elif kind == "cut":
            gone += wipe.part(tab, buck, lo, hi)
        else:
            take.part(tab, prop.base, buck, lo, hi)
    tab.head = num
    say.land(tab, prop.tag, num, add, gone)
