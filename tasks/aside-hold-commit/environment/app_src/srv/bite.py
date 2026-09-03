def chop(vis, inert, stops):
    hit = -1
    for st in stops:
        at = 0
        while True:
            at = vis.find(st, at)
            if at < 0:
                break
            if not any(inert[at:at + len(st)]):
                if hit < 0 or at < hit:
                    hit = at
                break
            at += 1
    if hit < 0:
        return vis, inert, False
    return vis[:hit], inert[:hit], True
