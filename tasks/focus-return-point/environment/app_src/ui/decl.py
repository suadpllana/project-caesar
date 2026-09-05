from ui.node import Ev

KEYS = ("tab", "back", "next", "prev")
ONE = ("want", "drop", "hide", "show", "off", "on", "shut", "open", "pick")


def flags(toks):
    fl, grp = [], None
    for t in toks:
        if t.startswith("grp="):
            grp = t[4:]
        else:
            fl.append(t)
    return fl, grp


def load(ui, lines):
    evs = []
    for raw in lines:
        toks = raw.split()
        if not toks:
            continue
        if toks[0] == "screen":
            ui.screen(toks[1])
        elif toks[0] == "w":
            fl, grp = flags(toks[3:])
            ui.make(toks[1], ui.holder(toks[2]), fl, grp)
        else:
            evs.append(toks)
    return evs


def event(ui, toks):
    ev = Ev(toks[0])
    k = ev.k
    if k in ("push", "pop"):
        ev.s = ui.scr[toks[1]]
    elif k in ONE:
        ev.w = ui.nd.get(toks[1])
    elif k == "add":
        ev.nm = toks[1]
        ev.p = ui.holder(toks[2])
        ev.at = int(toks[3])
        ev.fl, ev.grp = flags(toks[4:])
    elif k == "move":
        ev.w = ui.nd[toks[1]]
        ev.p = ui.holder(toks[2])
        ev.at = int(toks[3])
    elif k not in KEYS:
        raise ValueError(k)
    return ev
