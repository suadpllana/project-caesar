from ui import reach
from ui.node import Nd


class Pt:
    __slots__ = ("p", "i")

    def __init__(self, p, i):
        self.p = p
        self.i = i


class Keep:
    def __init__(self):
        self.ret = {}
        self.held = {}
        self.orig = None
        self.gone = {}

    def drop(self, nd, at):
        # Only the root of a dropped subtree needs recording: everything below it still
        # hangs off a detached parent whose child list is intact, so its own place can
        # be read off the parent when it is asked for.
        self.gone[nd] = (nd.par, at)

    def place(self, nd):
        """The point a gone widget stood at. For a screen root, the screen's return."""
        if nd.par is None:
            return self.ret.get(nd.scr)
        if nd in self.gone:
            p, at = self.gone[nd]
            return Pt(p, at)
        return Pt(nd.par, nd.par.kids.index(nd))

    def spot(self, ui, tgt):
        """Resolve a landing against the tree as it is now.

        Returns a live widget (which may or may not be able to take focus - the caller
        decides), a point whose container is live, or None.
        """
        while tgt is not None:
            if isinstance(tgt, Nd):
                if reach.alive(ui, tgt):
                    return tgt
                tgt = self.place(tgt)
            else:
                if reach.alive(ui, tgt.p):
                    return tgt
                tgt = self.place(tgt.p)
        return None
