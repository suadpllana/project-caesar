from led import cell, hold, say, tree


def drop(st, still):
    if tree.rooted(st, still):
        say.busy(st, still)
        return
    rec = st.stills.pop(still)
    cell.line(st, rec.owner).stills.remove(still)
    size = 0
    for b in rec.held.values():
        hold.thaw(b)
        if not hold.kept(b):
            size += b.size
    say.gone(st, still, size)
