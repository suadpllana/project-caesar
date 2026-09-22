from crd import book as bk
from crd import obs, tally, void


def watched(book, watch, store, out, moved):
    delta = {}
    for gid in book.credit(store, moved, delta):
        out.line("mark %d" % gid)
    for bar in watch.near(moved):
        if watch.fires(bar, store):
            out.line("fire %d" % bar.bid)
            for gid in void.fire(book, bar, delta):
                out.line("void %d" % gid)
    book.settle(delta)
    watch.refresh(store, moved)


def run(cfg, one, store, sums, out):
    book = bk.Book(one.goals)
    watch = obs.Watch(one.bars)
    start = store.mark()
    store.take()
    watch.base(store)
    used = 0
    closed = False
    for actions, done in one.steps:
        here = store.mark()
        short = False
        for op, key, val in actions:
            if used >= cfg.budget:
                short = True
                break
            if op == "put":
                store.put(key, val)
            else:
                store.cut(key)
            used += 1
        if short or not done:
            store.undo(here)
            if short:
                closed = True
                break
            continue
        watched(book, watch, store, out, store.take())
    if closed:
        store.undo(start)
    store.seal(start)
    store.take()
    tally.done(one, book, used, sums, out)
