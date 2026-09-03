from bay import cov, desc


# Can this parcel go up against this shown map, whole?
#
# Three cases per entry, and the order they are asked in is the point.
#
# The worker is already at or after the version named. Nothing to do for that
# entry, and nothing to ask about it either: the picture behind the version the
# worker actually holds stood up when that version went up, and the older one
# named here is not the one that will be shown.
#
# The worker holds something the named version does not stand after. The two are
# off on different sides of a common parent, so putting this one up would be
# going back. A parcel goes up whole or not at all, so that answer is the answer
# for the parcel, however well covered everything beside it is. It is not final
# for all time - the worker can settle the setting later, and then the entry is
# behind it - so the parcel stays in the bag.
#
# Otherwise the entry is ahead of what the worker shows, or the worker has never
# heard of the setting, and the question is whether the picture its writer was
# showing is covered.


def ripe(st, p, view):
    for s in p:
        v = p[s]
        cur = view.get(s, -1)
        if cur != -1:
            if desc.runs(st, cur, v):
                continue
            if not desc.runs(st, v, cur):
                return False
        if not cov.covers(st, st.vers[v].deps, view, p):
            return False
    return True
