from crd import book as bk
from crd import obs, tally, void


def seen(book, watch, store, out, moved):
    delta = {}
    for gid in book.credit(store, moved, delta):
        out.line("mark %d" % gid)
    for bar in watch.near(moved):
        if not watch.fires(bar, store):
            continue
        out.line("fire %d" % bar.bid)
        for gid in void.fire(book, bar, delta):
            out.line("void %d" % gid)
    book.settle(delta)
    watch.refresh(store, moved)


def run(cfg, one, store, sums, out):
    book = bk.Book(one.goals)
    watch = obs.Watch(one.bars)
    opened = store.mark()
    store.take()
    watch.base(store)
    spent = 0
    cut = False
    for actions, good in one.steps:
        began = store.mark()
        room = cfg.budget - spent
        take = actions if room >= len(actions) else actions[:max(room, 0)]
        for op, key, val in take:
            if op == "put":
                store.put(key, val)
            else:
                store.cut(key)
        spent += len(take)
        if len(take) != len(actions):
            store.undo(began)
            cut = True
            break
        if not good:
            store.undo(began)
            continue
        seen(book, watch, store, out, store.take())
    if cut:
        store.undo(opened)
    store.seal(opened)
    store.take()
    tally.done(one, book, spent, sums, out)
