def agree(fills):
    restored = []
    at = 0
    while fills:
        nxt = {f[at] if at < len(f) else None for f in fills}
        if len(nxt) == 1 and None not in nxt:
            restored.append(nxt.pop())
            at += 1
            continue
        return restored, [] if nxt == {None} else list(nxt)
    return restored, []
