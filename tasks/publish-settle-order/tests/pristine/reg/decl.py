from reg import tab


def unit(h, name):
    tab.get(h, name)


def need(h, name, other, hard):
    r = tab.get(h, name)
    tab.get(h, other)
    r.needs.append((other, hard))


def pub(h, name, sym, fall):
    tab.get(h, name).pubs.append((sym, fall))


def boot(h, name, sym):
    tab.get(h, name).boots.append(sym)
