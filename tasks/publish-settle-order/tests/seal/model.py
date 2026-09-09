"""The sealed implementation the graded traces are compared against.

Written from the frozen contract, not from the reference, and sharing no code with it. Where the
reference recurses through the dependency graph, this one walks an explicit stack; where the
reference hangs a serial on each record and keeps the live units in a list, this one numbers
publications and keeps no order list at all, addressing everything by publication id; where the
reference takes cascade candidates from a heap, this one keeps a list sorted by bisect. The two
agree on the shipped hand cases and on every generated program, which is evidence about the
contract rather than about one way of writing it down.

The rules, in the order they bite:

  * `act` and `open` both bring a unit up if it is not up and then add one direct hold. Bringing
    a unit up processes what it names - dependencies and ordering edges alike - in declaration
    order, skipping any that is already up or is itself part way up, then publishes the unit at
    the back of the order, then runs the unit's startup calls. A startup call therefore sees the
    order as it stands at that moment.
  * `act` publishes into no scope; every publication of one `open` activation belongs to one
    fresh scope. `act` on a unit that is up in a scope makes that publication public where it
    stands: same publication, same place in the order, visible to everyone from then on. `open`
    on a unit that is already up adds a hold and nothing else.
  * A call from a unit that is not up is not an event. A call whose use has not settled takes
    the first publisher of that name in publication order that the caller can see - a public
    publication, or one in the caller's own scope - and settles there, a fallback publication
    being a publisher like any other. A call that finds nothing settles nothing.
  * A settled use is never resolved again. It answers `run` while the publication it settled on
    is still up, and `dead` afterwards, including when a unit of the same name has come back.
  * `rel` drops one direct hold from a unit that is up and holds at least one, then sweeps. A
    unit is wanted while it holds at least one direct hold or any unit still up names it as a
    dependency; an ordering edge decides when its target comes up and keeps nothing afterwards.
    The sweep retires the last unwanted unit in publication order, applies that retirement, and
    looks again until nothing unwanted is left.
"""
import bisect


class _D:
    def __init__(self):
        self.needs = []
        self.pubs = []
        self.boots = []


class _S:
    def __init__(self):
        self.decl = {}
        self.at = {}
        self.name = {}
        self.den = {}
        self.hold = {}
        self.owed = {}
        self.idx = {}
        self.used = {}
        self.loose = []
        self.n = 0
        self.scopes = 0
        self.out = []


def _decl(st, name):
    d = st.decl.get(name)
    if d is None:
        d = _D()
        st.decl[name] = d
        st.at[name] = None
        st.hold[name] = 0
    return d


def _syms(d):
    return list(dict.fromkeys(p[0] for p in d.pubs))


def _hard(d):
    return list(dict.fromkeys(other for other, kind in d.needs if kind))


def _loosen(st, pid):
    """Remember a publication that may have stopped being wanted, newest first."""
    bisect.insort(st.loose, -pid)


def _wanted(st, pid):
    name = st.name[pid]
    return st.hold[name] > 0 or st.owed.get(name, 0) > 0


def _publish(st, name, den):
    st.n += 1
    pid = st.n
    st.at[name] = pid
    st.name[pid] = name
    st.den[pid] = den
    for sym in _syms(st.decl[name]):
        st.idx.setdefault((den, sym), []).append(pid)
    for other in _hard(st.decl[name]):
        st.owed[other] = st.owed.get(other, 0) + 1
    if not _wanted(st, pid):
        _loosen(st, pid)
    st.out.append("up " + name)


def _retire(st, pid):
    name = st.name.pop(pid)
    den = st.den.pop(pid)
    st.at[name] = None
    for sym in _syms(st.decl[name]):
        lst = st.idx.get((den, sym))
        if lst and pid in lst:
            lst.remove(pid)
    for other in _hard(st.decl[name]):
        left = st.owed.get(other, 0) - 1
        st.owed[other] = left
        if left <= 0 and st.at.get(other) is not None:
            _loosen(st, st.at[other])
    st.out.append("down " + name)


def _promote(st, pid):
    was = st.den[pid]
    if was is None:
        return
    name = st.name[pid]
    for sym in _syms(st.decl[name]):
        lst = st.idx.get((was, sym))
        if lst and pid in lst:
            lst.remove(pid)
        st.idx.setdefault((None, sym), []).append(pid)
        st.idx[(None, sym)].sort()
    st.den[pid] = None


def _visible(st, pid):
    den = st.den[pid] if pid in st.den else None
    return (None,) if den is None else (None, den)


def _call(st, name, sym):
    pid = st.at.get(name)
    if pid is None:
        return
    key = (pid, sym)
    if key in st.used:
        tgt = st.used[key]
        if tgt in st.name:
            st.out.append("run %s %s %s" % (name, sym, st.name[tgt]))
        else:
            st.out.append("dead %s %s" % (name, sym))
        return
    best = None
    for den in _visible(st, pid):
        lst = st.idx.get((den, sym))
        if lst and (best is None or lst[0] < best):
            best = lst[0]
    if best is None:
        st.out.append("miss %s %s" % (name, sym))
        return
    st.used[key] = best
    st.out.append("run %s %s %s" % (name, sym, st.name[best]))


def _bring(st, name, wide):
    _decl(st, name)
    if st.at[name] is not None:
        if wide:
            _promote(st, st.at[name])
        st.hold[name] += 1
        return
    st.scopes += 1
    den = None if wide else st.scopes
    busy = {name}
    stack = [[name, 0]]
    while stack:
        top = stack[-1]
        needs = st.decl[top[0]].needs
        if top[1] < len(needs):
            other = needs[top[1]][0]
            top[1] += 1
            _decl(st, other)
            if st.at[other] is None and other not in busy:
                busy.add(other)
                stack.append([other, 0])
            continue
        _publish(st, top[0], den)
        for sym in st.decl[top[0]].boots:
            _call(st, top[0], sym)
        busy.discard(top[0])
        stack.pop()
    st.hold[name] += 1


def _release(st, name):
    _decl(st, name)
    pid = st.at[name]
    if pid is None or st.hold[name] <= 0:
        return
    st.hold[name] -= 1
    _loosen(st, pid)
    while st.loose:
        pid = -st.loose.pop(0)
        if pid not in st.name or _wanted(st, pid):
            continue
        _retire(st, pid)


def expect(lines):
    """Run a program and return the lines the host must print."""
    st = _S()
    for ln in lines:
        op = ln.split()
        k = op[0]
        if k == "unit":
            _decl(st, op[1])
        elif k == "dep":
            _decl(st, op[2])
            _decl(st, op[1]).needs.append((op[2], True))
        elif k == "pre":
            _decl(st, op[2])
            _decl(st, op[1]).needs.append((op[2], False))
        elif k == "pub":
            _decl(st, op[1]).pubs.append((op[2], False))
        elif k == "fall":
            _decl(st, op[1]).pubs.append((op[2], True))
        elif k == "boot":
            _decl(st, op[1]).boots.append(op[2])
        elif k == "act":
            _bring(st, op[1], True)
        elif k == "open":
            _bring(st, op[1], False)
        elif k == "call":
            _decl(st, op[1])
            _call(st, op[1], op[2])
        elif k == "rel":
            _release(st, op[1])
        else:
            raise ValueError(k)
    return st.out
