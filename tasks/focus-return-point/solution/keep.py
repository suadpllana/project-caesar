"""Where focus goes when it has nowhere to be yet: the deferred landings.

Three things are recorded and none of them is resolved when it is recorded.

  ret    per screen, where focus was on the screen underneath at the moment this screen
         went on top - the widget that held it, or, if nothing did, the place the previous
         focus stood.
  held   per screen, the most recent request for a widget on that screen made while the
         screen was not on top.
  orig   where focus stood when it was last lost: the widget that held it, whether or not
         that widget still exists.

The shipped keep.py resolved each of these at the moment it was recorded or at the moment
the tree changed - it turned a disabled restore target into "nothing" when the widget was
disabled, dropped a request the moment it could not be honoured, and started every Tab
from the top of the screen once focus was lost. Every one of those is right until the
thing it gave up on comes back: a target re-enabled before the pop, a requested widget
shown again before its screen returns, a widget re-shown at the place it stood. So nothing
here decides anything until a landing is actually needed, and then it asks the tree as it
is at that moment.

A landing is one of three shapes: a widget, a point, or None (no screen at all). A widget
that is gone becomes the point it stood at; a point whose container is gone becomes the
point the container stood at; and the point of a screen's root is the screen's own return
record, which is what makes a return through a screen popped out of order the same walk as
a return through a dropped container. That last identity is the whole of the out-of-order
rule, and it is why the records are kept per screen rather than on a stack: a stack pops
the wrong record the moment a screen underneath goes first.
"""

from ui import reach
from ui.node import Nd


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
            return ("pt", p, at)
        return ("pt", nd.par, nd.par.kids.index(nd))

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
                if reach.alive(ui, tgt[1]):
                    return tgt
                tgt = self.place(tgt[1])
        return None
