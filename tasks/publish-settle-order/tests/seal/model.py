"""The sealed implementation the graded traces are compared against.

Written from the frozen contract, not from the reference, and sharing no code with it. Where the
reference recurses through the dependency graph and marks each publication with a fresh object,
this one walks an explicit stack and numbers every publication, keeps one flat table of settled
uses keyed by (publication, name) instead of a table per record, and takes the retirement
candidate by scanning the order from the back rather than keeping the last hit of a forward
scan. Agreement between the two on a hand case and on every generated program is therefore
evidence about the contract rather than about one way of writing it down.

The rules, in the order they bite:

  * `act` brings a unit up if it is not up, then adds one direct hold either way. Bringing a
    unit up processes what it names - dependencies and ordering edges alike - in declaration
    order, skipping any that is already up or is itself part way up, then publishes the unit at
    the back of the order, then runs the unit's startup calls. A startup call therefore sees the
    order as it stands at that moment.
  * A call from a unit that is not up is not an event. A call whose use has not settled takes
    the first publisher of that name in publication order - a fallback publication is a
    publisher like any other - and settles there. A call that finds nothing settles nothing.
  * A settled use is never resolved again. It answers `run` while the publication it settled on
    is still up, and `dead` afterwards, including when a unit of the same name has come back.
  * `rel` drops one direct hold from a unit that is up and holds at least one, then sweeps. A
    unit is wanted while it holds at least one direct hold or any unit still up names it as a
    dependency. An ordering edge decides when its target comes up and keeps nothing afterwards.
    The sweep retires the last unwanted unit in publication order, applies that retirement, and
    looks again until a pass finds none.
"""


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
        self.hold = {}
        self.order = []
        self.idx = {}
        self.used = {}
        self.n = 0
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


def _publish(st, name):
    st.n += 1
    pid = st.n
    st.at[name] = pid
    st.name[pid] = name
    st.order.append(pid)
    for s in _syms(st.decl[name]):
        st.idx.setdefault(s, []).append(pid)
    st.out.append("up " + name)


def _retire(st, pid):
    name = st.name.pop(pid)
    st.order.remove(pid)
    st.at[name] = None
    for s in _syms(st.decl[name]):
        lst = st.idx.get(s)
        if lst and pid in lst:
            lst.remove(pid)
    st.out.append("down " + name)


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
    lst = st.idx.get(sym)
    if not lst:
        st.out.append("miss %s %s" % (name, sym))
        return
    tgt = lst[0]
    st.used[key] = tgt
    st.out.append("run %s %s %s" % (name, sym, st.name[tgt]))


def _bring(st, name):
    _decl(st, name)
    if st.at[name] is None:
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
            _publish(st, top[0])
            for s in st.decl[top[0]].boots:
                _call(st, top[0], s)
            busy.discard(top[0])
            stack.pop()
    st.hold[name] += 1


def _wanted(st, pid):
    name = st.name[pid]
    if st.hold[name] > 0:
        return True
    for other in st.order:
        if other == pid:
            continue
        for named, kind in st.decl[st.name[other]].needs:
            if kind and named == name:
                return True
    return False


def _release(st, name):
    _decl(st, name)
    if st.at[name] is None or st.hold[name] <= 0:
        return
    st.hold[name] -= 1
    while True:
        go = None
        for pid in reversed(st.order):
            if not _wanted(st, pid):
                go = pid
                break
        if go is None:
            return
        _retire(st, go)


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
            _bring(st, op[1])
        elif k == "call":
            _decl(st, op[1])
            _call(st, op[1], op[2])
        elif k == "rel":
            _release(st, op[1])
        else:
            raise ValueError(k)
    return st.out
