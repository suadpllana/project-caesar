"""The sealed implementation the graded traces are compared against.

Written from the frozen contract, not from the reference, and sharing no code with it. Where the
reference recurses through the dependency graph, this one walks an explicit stack; where the
reference hangs a tuple key on each record and keeps the live units in a linked order, this one
numbers publications, keys them by exact fractions and keeps a sorted list of live keys; where
the reference keeps cascade candidates in a heap, this one keeps a list sorted by bisect. The two
agree on the shipped hand cases and on every generated program, which is evidence about the
contract rather than about one way of writing it down.

The rules, in the order they bite:

  * `act` and `open` both bring a unit up if it is not up and then add one direct hold. Bringing
    a unit up processes what it names - dependencies and ordering edges alike - in declaration
    order, skipping any that is already up or is itself part way up, then publishes the unit at
    the back of the order, then runs the unit's startup calls. A startup call therefore sees the
    order as it stands at that moment. No unit names itself.
  * `act` publishes into no scope; every publication of one `open` activation belongs to one
    fresh scope. A unit reads the public publications and the ones in the scope it was brought
    up into, for as long as it is up. `act` on a unit that is up in a scope makes that
    publication public where it stands - same publication, same place in the order, visible to
    everyone from then on - and changes nothing about what the unit itself reads. `open` on a
    unit that is already up adds a hold and nothing else.
  * A call from a unit that is not up is not an event. A call whose use has not settled takes
    the first publisher of that name in publication order that the caller can see and settles
    there, a fallback publication being a publisher like any other.
  * A call that finds nothing looks for the first unit marked `auto` - in the order the marks
    were made - that publishes the name and is neither up nor part way up. If there is none, the
    call is a miss and settles nothing. If there is one, the call brings it up as if the caller
    had named it as a dependency: what comes up is published directly ahead of the caller in the
    publication order, in the order it comes up, into the scope the caller reads (public when the
    caller reads no scope), with its startup calls run as in any activation, with no hold taken,
    and the caller keeps the unit it brought up as a dependency would until the caller goes down.
    The call is then answered by the ordinary rule over the order as it now stands, which need
    not name the unit brought up.
  * A settled use is never resolved again. It answers `run` while the publication it settled on
    is still up, and `dead` afterwards, including when a unit of the same name has come back.
  * `rel` drops one direct hold from a unit that is up and holds at least one, then sweeps. A
    unit is wanted while it holds at least one direct hold, or any unit still up names it as a
    dependency, or any unit still up brought it up as the answer to a call; an ordering edge
    decides when its target comes up and keeps nothing afterwards; two units that are up and
    name each other as dependencies keep each other up. The sweep retires the last unwanted unit
    in publication order, applies that retirement, and looks again until nothing unwanted is
    left.
"""
import bisect
from fractions import Fraction


class _D:
    def __init__(self):
        self.needs = []
        self.pubs = []
        self.boots = []
        self.auto = False


class _S:
    def __init__(self):
        self.decl = {}
        self.at = {}
        self.name = {}
        self.key = {}
        self.seq = []
        self.den = {}
        self.home = {}
        self.hold = {}
        self.owed = {}
        self.idx = {}
        self.used = {}
        self.bound = {}
        self.loose = []
        self.busy = set()
        self.autos = []
        self.n = 0
        self.top = 0
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


def _mark(st, name):
    d = _decl(st, name)
    if not d.auto:
        d.auto = True
        st.autos.append(name)


def _syms(d):
    return list(dict.fromkeys(p[0] for p in d.pubs))


def _hard(d):
    return list(dict.fromkeys(other for other, kind in d.needs if kind))


def _loosen(st, pid):
    """Remember a publication that may have stopped being wanted, last in the order first."""
    bisect.insort(st.loose, (-st.key[pid], pid))


def _wanted(st, pid):
    name = st.name[pid]
    return st.hold[name] > 0 or st.owed.get(name, 0) > 0


def _place(st, before):
    """The key of a publication appended to the order, or placed directly ahead of `before`."""
    if before is None:
        st.top += 1
        return Fraction(st.top)
    k = st.key[before]
    i = bisect.bisect_left(st.seq, (k, before))
    pred = st.seq[i - 1][0] if i > 0 else k - 1
    return (pred + k) / 2


def _publish(st, name, den, home, before):
    st.n += 1
    pid = st.n
    key = _place(st, before)
    st.at[name] = pid
    st.name[pid] = name
    st.key[pid] = key
    bisect.insort(st.seq, (key, pid))
    st.den[pid] = den
    st.home[pid] = home
    st.bound[pid] = []
    for sym in _syms(st.decl[name]):
        bisect.insort(st.idx.setdefault((den, sym), []), (key, pid))
    for other in _hard(st.decl[name]):
        st.owed[other] = st.owed.get(other, 0) + 1
    if not _wanted(st, pid):
        _loosen(st, pid)
    st.out.append("up " + name)


def _unlist(lst, item):
    i = bisect.bisect_left(lst, item)
    if i < len(lst) and lst[i] == item:
        del lst[i]


def _retire(st, pid):
    name = st.name.pop(pid)
    key = st.key.pop(pid)
    den = st.den.pop(pid)
    st.home.pop(pid)
    st.at[name] = None
    _unlist(st.seq, (key, pid))
    for sym in _syms(st.decl[name]):
        lst = st.idx.get((den, sym))
        if lst:
            _unlist(lst, (key, pid))
    for other in _hard(st.decl[name]) + st.bound.pop(pid):
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
    key = st.key[pid]
    for sym in _syms(st.decl[name]):
        lst = st.idx.get((was, sym))
        if lst:
            _unlist(lst, (key, pid))
        bisect.insort(st.idx.setdefault((None, sym), []), (key, pid))
    st.den[pid] = None


def _visible(st, pid):
    home = st.home[pid]
    return (None,) if home is None else (None, home)


def _first(st, pid, sym):
    best = None
    for den in _visible(st, pid):
        lst = st.idx.get((den, sym))
        if lst and (best is None or lst[0][0] < best[0]):
            best = lst[0]
    return None if best is None else best[1]


def _candidate(st, sym):
    for name in st.autos:
        if st.at[name] is None and name not in st.busy and sym in _syms(st.decl[name]):
            return name
    return None


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
    best = _first(st, pid, sym)
    if best is None:
        cand = _candidate(st, sym)
        if cand is not None:
            _walk(st, cand, st.home[pid], pid)
            st.bound[pid].append(cand)
            st.owed[cand] = st.owed.get(cand, 0) + 1
            best = _first(st, pid, sym)
    if best is None:
        st.out.append("miss %s %s" % (name, sym))
        return
    st.used[key] = best
    st.out.append("run %s %s %s" % (name, sym, st.name[best]))


def _walk(st, root, den, before):
    st.busy.add(root)
    stack = [[root, 0]]
    while stack:
        top = stack[-1]
        needs = st.decl[top[0]].needs
        if top[1] < len(needs):
            other = needs[top[1]][0]
            top[1] += 1
            _decl(st, other)
            if st.at[other] is None and other not in st.busy:
                st.busy.add(other)
                stack.append([other, 0])
            continue
        _publish(st, top[0], den, den, before)
        for sym in st.decl[top[0]].boots:
            _call(st, top[0], sym)
        st.busy.discard(top[0])
        stack.pop()


def _bring(st, name, wide):
    _decl(st, name)
    if st.at[name] is not None:
        if wide:
            _promote(st, st.at[name])
        st.hold[name] += 1
        return
    if wide:
        den = None
    else:
        st.scopes += 1
        den = st.scopes
    _walk(st, name, den, None)
    st.hold[name] += 1


def _release(st, name):
    _decl(st, name)
    pid = st.at[name]
    if pid is None or st.hold[name] <= 0:
        return
    st.hold[name] -= 1
    _loosen(st, pid)
    while st.loose:
        pid = st.loose.pop(0)[1]
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
        elif k == "auto":
            _mark(st, op[1])
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
