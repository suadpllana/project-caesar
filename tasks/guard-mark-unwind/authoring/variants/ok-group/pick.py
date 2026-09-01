"""Which mark, if any, reaches this fiber at this checkpoint.

Two corrections against the shipped version.

The window. Scanning outward from the fiber, the first guard carrying a shield is the
last one the fiber can still see: everything enclosing that guard is hidden. The guard
holding the shield is inside the window, not outside it, so its own mark still reaches
the fiber. The shipped version skips it, which is why a fiber that shields a guard and
then marks that same guard runs on forever.

The choice inside the window. When several guards in the window are marked, the mark
that reaches the fiber is the outermost one. Attributing to the innermost is what a
runtime built around a single cancellation token does, and it is wrong here for a reason
that only shows up one op later: the innermost guard then takes the exception at its own
boundary, the fiber lands back in the enclosing guard which is still marked, and it runs
whatever sits between there and the next checkpoint. Blocks are not checkpoints, so those
tokens are emitted inside a guard that has already been marked.

There is no per-fiber memory here on purpose. A mark stays raised until the guard closes,
so the answer is recomputed from scratch every time it is asked and the same guard can be
delivered to the same fiber over and over - once at the checkpoint that starts the
unwinding, again inside a cleanup block, again when a band the fiber cannot leave finally
lets go.
"""


def wall(ch):
    out = []
    for g in reversed(ch):
        out.append(g)
        if g.sh:
            break
    return out


def pick(f, ch):
    best = None
    for g in wall(ch):
        if g.hit:
            best = g
    return best
