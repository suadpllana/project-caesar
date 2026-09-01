"""Where an in-flight cut comes to rest, and what happens when a second one lands.

The shipped version stamps the guard that was picked onto the cut and stops at the guard
whose identity matches. That is the natural implementation and it is wrong whenever the
set of marked guards changes between the checkpoint that raised the cut and the boundary
that would take it - a deadline crossing while a cleanup block runs, a sibling failing
while the fiber sits at a band it is not allowed to leave. The stamp is then stale: the
guard it names takes the cut, the fiber resumes inside an enclosing guard that has been
marked in the meantime, and it runs blocks there.

So the boundary is decided from the marks that stand at the moment the guard closes, not
from the ones that stood when the cut was raised. This guard takes the cut when it is
marked and nothing still visible outside it is marked; visible means the same window the
delivery side uses, computed on the chain that remains now that this guard has been
popped. When something outside is marked the cut keeps travelling, which is what stops
the fiber from resuming inside it.

Nothing here clears a mark. The shipped version does, which turns the whole runtime
edge-triggered: after one delivery the guard goes quiet, and a fiber that shields itself
through a cleanup block never hears about the mark again once the shield drops.

blend decides which of two in-flight exceptions survives, and only a cleanup block can
produce the collision. The newer one wins, the same way a raise inside a finally clause
replaces what was already propagating.
"""


def wall(ch):
    out = []
    for g in reversed(ch):
        out.append(g)
        if g.sh:
            break
    return out


def stops(g, ch, gg):
    if not g.hit:
        return False
    for h in wall(ch):
        if h.hit:
            return False
    return True


def blend(old, new):
    return new
