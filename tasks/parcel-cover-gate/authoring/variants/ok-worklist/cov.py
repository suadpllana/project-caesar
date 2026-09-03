from bay import desc


# Is everything the writer of a version was showing already covered?
#
# `deps` is that writer's whole shown map at the moment it wrote. A setting in
# it is covered when the taker shows a version that is the one named or grew out
# of it. Showing a later, unrelated child of the same parent is not covering: it
# is a different branch, and the picture the writer had is not one this worker
# can be brought to.
#
# The parcel under test counts towards its own coverage. A parcel is a picture of
# one band as one worker held it, so its entries are consistent with each other
# by construction, and a chain inside a single parcel - one setting written after
# another was shown, both of them in that band - would otherwise never come out
# of the bag, because nothing outside the parcel is ever going to deliver the
# earlier entry that the parcel already carries. What must not count is the rest
# of the bag: a parcel still waiting is not shown, and what is not shown covers
# nothing.


def covers(st, deps, view, ent):
    for s in deps:
        v = deps[s]
        if s in view and desc.runs(st, view[s], v):
            continue
        if s in ent and desc.runs(st, ent[s], v):
            continue
        return False
    return True
