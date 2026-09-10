def onloop(rel):
    for start in rel:
        path = [start]
        seen = {start}
        found = walk(rel, start, start, path, seen)
        if found:
            return found
    return []


def walk(rel, start, node, path, seen):
    for step in rel.get(node, ()):
        if step == start:
            return list(path)
        if step in seen or step not in rel:
            continue
        seen.add(step)
        path.append(step)
        got = walk(rel, start, step, path, seen)
        if got:
            return got
        path.pop()
    return []


def pick(txs):
    best = None
    for t in txs:
        if best is None or t.num > best.num:
            best = t
    return best
