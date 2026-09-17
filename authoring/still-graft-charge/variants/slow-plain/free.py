from led import cell, hold, say, tree


def drop(st, still):
    if tree.rooted(st, still):
        say.busy(st, still)
        return
    rec = st.stills.pop(still)
    cell.line(st, rec.owner).stills.remove(still)
    size = 0
    for b in rec.held.values():
        hold.off(b, rec.owner)
        if not hold.who(b):
            size += b.size
    say.gone(st, still, size)
