def bad(cat, heap, con, tn, k):
    row = heap.get(tn, k)
    if row is None:
        return False
    v = row[cat.tables[tn].pos[con.col]]
    if con.kind == "check":
        if con.test == "notnull":
            return v is None
        return v is None or v < con.floor
    return v is not None and not heap.has(con.parent, v)


def scan(cat, heap, con):
    return [k for k in heap.keys(con.table) if bad(cat, heap, con, con.table, k)]


def first(cat, heap, cons):
    for con in cons:
        hits = scan(cat, heap, con)
        if hits:
            return (con.name, con.table, hits[0])
    return None
