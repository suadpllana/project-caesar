from led import say


def shut(store, t):
    if t.bad:
        return say.shut_no(t.num)
    if t.taken.moved(store, t.wrote):
        return say.shut_no(t.num)
    if t.taken.stale(store):
        return say.shut_no(t.num)
    held = {}
    for k in t.wrote:
        held[k] = t.held.at(k, t.taken)
    return say.shut_ok(t.num, store.write(t.wrote, held))
