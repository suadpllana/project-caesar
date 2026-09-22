from plan.span import ends, last, takes


def reach(pp):
    # Nothing that ends before the corrected partition can read it, so the scan starts at its
    # end and walks every step partition from there to now in time order.
    src, i = pp.fix
    start = ends(pp, src, i)
    hit = {pp.fix}
    todo = []
    for name in pp.names:
        if name in pp.reads:
            first = start - 1 if pp.grain[name] == "h" else (start - 1) // 24
            for j in range(max(0, first), last(pp, name) + 1):
                todo.append((ends(pp, name, j), pp.pos[name], name, j))
    todo.sort()
    for _end, _pos, name, j in todo:
        for _kind, s, parts in takes(pp, name, j):
            if any((s, p) in hit for p in parts):
                hit.add((name, j))
                break
    return hit
