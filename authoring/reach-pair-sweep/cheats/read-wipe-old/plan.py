"""Which objects start the walk, which differs by collection kind.

A full collection starts from everything named: frame slots, the global table, the handle stack.
A minor collection starts from the nursery ones among those - old objects are live by assumption
and are never traced - and must add the nursery objects reachable from old space, which is the
only reason the remembered set exists.

The remembered set is a hint, not an answer. `mem/rset.py` records a (source, field, value) triple when a
field of an OLD object is given a nursery value, and never revisits it afterwards. The value in
the triple is the value the field had at the moment of the write, and nothing keeps it current:
overwrite the field and the old triple stays, naming an object nothing points at any more. An
entry can also outlive its source, which a later full collection may have released. So the
triple says where to look and the field's value now is the answer - taking the recorded value
keeps dead objects alive, and ignoring the set loses live ones.
"""
from mem import heap, roots as rootsrc


def roots(h, full):
    named = rootsrc.named(h)
    if full:
        return sorted(set(named))

    out = [i for i in named if h.objs[i].space == heap.NURSERY]
    for src, fld, was in sorted(h.rset):
        if src not in h.objs:
            continue
        val = h.objs[src].flds.get(fld)
        if val is None or val not in h.objs:
            continue
        if h.objs[val].space == heap.NURSERY:
            out.append(val)
    return sorted(set(out))
