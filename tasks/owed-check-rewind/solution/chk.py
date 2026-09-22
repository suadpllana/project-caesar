def broken(cat, heap, con, tn, k):
    """Does row k of tn violate con? A missing row violates nothing; min never fails on null."""
    row = heap.get(tn, k)
    if row is None:
        return False
    v = row[cat.tables[tn].pos[con.col]]
    if con.kind == "fk":
        return v is not None and not heap.has(con.parent, v)
    if con.test == "notnull":
        return v is None
    return v is not None and v < con.floor


def stranded(heap, fk, k):
    """Is parent key k left behind by fk: no parent row has it and some child still holds it?"""
    return not heap.has(fk.parent, k) and heap.held_by_any(fk, k)


def still(cat, heap, entry):
    """Is an owed entry still a violation? Its table says which side it names."""
    con = cat.con(entry[0])
    if con.kind == "fk" and entry[1] == con.parent:
        return stranded(heap, con, entry[2])
    return broken(cat, heap, con, entry[1], entry[2])
