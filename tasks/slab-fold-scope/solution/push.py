from tab import lay, say, take, wipe


def once(tab, prop, view, head, num):
    add = gone = 0
    made = False
    for kind, buck, lo, hi in prop.parts:
        if kind == 'put':
            add += lay.part(tab, num, buck, lo, hi)
            made = True
        elif kind == 'cut':
            gone += wipe.part(tab, buck, lo, hi)
        elif take.part(tab, view, head, buck, lo, hi):
            made = True
    return add, gone, made


def run(tab, prop):
    head = dict(tab.buck)
    view = dict(prop.root)
    number, first = tab.head + 1, tab.next
    while True:
        try:
            added, removed, made = once(tab, prop, view, head, number)
            break
        except take.Again as clash:
            tab.buck = dict(head)
            tab.next = first
            if not take.refresh(view, head, clash.buck, clash.sources):
                tab.out.append('clash %s' % prop.tag)
                return
    if not made and not removed:
        tab.buck = head
        tab.next = first
        say.void(tab, prop.tag)
        return
    tab.head = number
    say.land(tab, prop.tag, number, added, removed)
