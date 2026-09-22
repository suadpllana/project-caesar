import bisect


def down(tr, key):
    spine = [tr.root]
    slot = []
    while True:
        page = tr.at(spine[-1])
        if page.leaf:
            return spine, slot
        i = bisect.bisect_right(page.seps, key)
        slot.append(i)
        spine.append(page.kids[i])
