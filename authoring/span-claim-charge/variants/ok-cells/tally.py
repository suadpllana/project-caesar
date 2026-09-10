"""The charges, carried forward; the family settled from the sorted stamp paths of the standing lines."""
import bisect

from store import line as lines


def setup(st):
    return None


def _relca(st, sp):
    new = lines.meet(st, sp.paths[0], sp.paths[-1]) if sp.paths else None
    if new is sp.lca:
        return
    if sp.lca is not None:
        old = lines.deepest(st, sp.lca.path)
        if old is not None:
            old.lcat -= sp.wide
    if new is not None:
        new.lcat += sp.wide
    sp.lca = new


def _pair(st, pa, pb, delta):
    z = lines.meet(st, pa, pb)
    if z is not None:
        z.pair += delta


def gain(st, line, sp):
    line.ref += sp.wide
    line.own.add(sp)
    if len(sp.by) == 1:
        line.excl += sp.wide
    elif len(sp.by) == 2:
        for other in sp.by:
            if other is not line:
                other.excl -= sp.wide
    paths = sp.paths
    j = bisect.bisect_left(paths, line.path)
    if 0 < j < len(paths):
        _pair(st, paths[j - 1], paths[j], -sp.wide)
    paths.insert(j, line.path)
    if j:
        _pair(st, paths[j - 1], line.path, sp.wide)
    if j + 1 < len(paths):
        _pair(st, line.path, paths[j + 1], sp.wide)
    _relca(st, sp)


def lose(st, line, sp):
    line.ref -= sp.wide
    line.own.discard(sp)
    if not sp.by:
        line.excl -= sp.wide
    elif len(sp.by) == 1:
        for other in sp.by:
            other.excl += sp.wide
    paths = sp.paths
    j = bisect.bisect_left(paths, line.path)
    if j:
        _pair(st, paths[j - 1], line.path, -sp.wide)
    if j + 1 < len(paths):
        _pair(st, line.path, paths[j + 1], -sp.wide)
    paths.pop(j)
    if 0 < j < len(paths):
        _pair(st, paths[j - 1], paths[j], sp.wide)
    _relca(st, sp)


def charge(st, name):
    line = st.lines.get(name)
    if line is None:
        return "nosuch"
    return (line.ref, line.excl)


def gone(st, names):
    want = set()
    for name in names:
        line = st.lines.get(name)
        if line is None:
            return "nosuch"
        want.add(line)
    rel = 0
    seen = set()
    for line in want:
        for sp in line.own:
            if sp in seen:
                continue
            seen.add(sp)
            if want.issuperset(sp.by):
                rel += sp.wide
    return (rel,)


def family(st, name):
    line = st.lines.get(name)
    if line is None:
        return "nosuch"
    ref = 0
    excl = 0
    for z in lines.kin(st, line):
        ref += z.ref - z.pair
        excl += z.lcat
    return (ref, excl)
