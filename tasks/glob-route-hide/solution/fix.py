"""The least fixed point, over every module at once.

What a module holds is a set of bindings - (item, name) pairs - each with the region it can be
seen from. Every rule is monotone once hiding is decided by lines: a glob can only add, a wider
route can only widen, and the least fixed point is what chains of lines ending at item lines
reach. So the whole program is solved by starting every module from its own items and
re-deriving a module whenever something it reads from has grown, until nothing grows.

The textbook alternative - one lookup per (module, name) pair - is exact and far too slow on
the large programs: when every module reads its parent and re-exports its children the tree is
one cycle of globs, every module holds every name, and pair-by-pair work is quadratic. Holding
all of a module's bindings as one integer per region depth moves every name in one operation,
and the per-module mask of its own names keeps each name's cut exact.
"""
from collections import deque

from fe import glob, own, vis


class Tab:
    __slots__ = ("bit", "ids", "nmask", "mine", "cs", "top")

    def __init__(self):
        self.bit = {}
        self.ids = {}
        self.nmask = {}
        self.mine = {}
        self.cs = {}
        self.top = {}


def settle(prog):
    tab = Tab()
    own.alloc(prog, tab)
    readers = {}
    bases = {}
    for path in prog.order:
        tab.top[path] = vis.dep(path)
        mask = 0
        for name in own.names(prog, path):
            mask |= tab.nmask.get(name, 0)
        tab.mine[path] = mask
        bases[path] = own.base(prog, tab, path)
        tab.cs[path] = list(bases[path])
        for ln in own.lines(prog, path) + glob.lines(prog, path):
            if ln.k != "item" and ln.src in prog.mods:
                readers.setdefault(ln.src, set()).add(path)
    work = deque(prog.order)
    queued = set(prog.order)
    while work:
        path = work.popleft()
        queued.discard(path)
        new = list(bases[path])
        own.gives(prog, tab, path, new)
        glob.gives(prog, tab, path, new)
        if new != tab.cs[path]:
            tab.cs[path] = new
            for r in readers.get(path, ()):
                if r not in queued:
                    queued.add(r)
                    work.append(r)
    return tab
