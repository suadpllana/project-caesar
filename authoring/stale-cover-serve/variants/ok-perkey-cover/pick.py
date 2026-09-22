
def at(tb, lo, hi, s, now):
    floor = now - s
    if floor < 0:
        floor = 0
    width = hi - lo + 1
    over = [[] for _ in range(width)]
    for st in tb.near(lo, hi):
        top = now if st.died < 0 else st.died
        if top < floor:
            continue
        low = st.born
        if low < floor:
            low = floor
        if low > top:
            continue
        a = st.lo if st.lo > lo else lo
        b = st.hi if st.hi < hi else hi
        for k in range(a - lo, b - lo + 1):
            over[k].append((low, top))
    marks = []
    for box in over:
        if not box:
            return None
        box.sort()
        run = [box[0][0], box[0][1]]
        for low, top in box[1:]:
            if low <= run[1] + 1:
                if top > run[1]:
                    run[1] = top
            else:
                marks.append((run[0], 1))
                marks.append((run[1] + 1, -1))
                run = [low, top]
        marks.append((run[0], 1))
        marks.append((run[1] + 1, -1))
    marks.sort()
    best = None
    live = 0
    i = 0
    total = len(marks)
    while i < total:
        here = marks[i][0]
        while i < total and marks[i][0] == here:
            live += marks[i][1]
            i += 1
        if live == width and here <= now:
            end = marks[i][0] - 1 if i < total else now
            if end > now:
                end = now
            if end >= here and (best is None or end > best):
                best = end
    return best
