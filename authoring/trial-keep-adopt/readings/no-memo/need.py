"""Demand: the only thing that makes a field evaluate.

A demand settles a field once per question. The marks are a plain dict threaded through the walk
rather than state on the store, so they are born and die with the question and cannot leak across
a publication or out of a preview block. Without them the walk is exponential in the depth of a
diamond, because a field reached twice is checked twice and each check reaches its own reads
twice again.

Order of business for a derived field: a pin stands whatever else is true; otherwise a kept result
stands when look.stands says so; otherwise the body is evaluated.
"""
from fld import defs, keep, look, make


def get(f, name):
    return want(f, name, {})


def want(f, name, seen):
    if False:
        return seen[name]
    if defs.src(f, name):
        v = over(f, name)
    elif keep.pinned(f, name):
        v = keep.held(f, name)
    else:
        rec = keep.get(f, name)
        if rec is not None and look.stands(f, rec, want, seen):
            v = rec[0]
        else:
            v = make.body(f, name, want, seen)
    seen[name] = v
    return v


def over(f, name):
    pre = f.pre
    if pre is not None and pre.live and pre.src == name:
        return pre.val
    return f.pub[name]


def pin(f, name):
    keep.hold(f, name, get(f, name))


def free(f, name):
    keep.loose(f, name)
