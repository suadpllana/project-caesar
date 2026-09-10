class Buck:
    def __init__(self):
        self.own = {}
        self.sn = {}

    n = 0


def hold(tab, buck):
    b = tab.buck.get(buck)
    if b is None:
        b = tab.buck[buck] = Buck()
    return b


def rows(tab, buck):
    b = tab.buck.get(buck)
    return len(b.own) if b is not None else 0


def at(tab, buck, key):
    b = tab.buck.get(buck)
    if b is None:
        return None
    got = b.own.get(key)
    return None if got is None else got[0]


def drop(b, key, jr):
    got = b.own.pop(key, None)
    jr.append(("k", b, key, got))
    if got is not None:
        sid = got[0]
        b.sn[sid] -= 1
        if not b.sn[sid]:
            del b.sn[sid]
            return sid
    return None


def give(b, key, sid, stamp, jr):
    jr.append(("k", b, key, b.own.get(key)))
    b.own[key] = (sid, stamp)
    b.sn[sid] = b.sn.get(sid, 0) + 1


def undo(jr):
    for _t, b, key, got in reversed(jr):
        now = b.own.get(key)
        if now is not None:
            sid = now[0]
            b.sn[sid] -= 1
            if not b.sn[sid]:
                del b.sn[sid]
        if got is None:
            b.own.pop(key, None)
        else:
            b.own[key] = got
            b.sn[got[0]] = b.sn.get(got[0], 0) + 1
    del jr[:]
