"""The line procedure, and the take that every other rule is written against.

A take is settled level by level from the store inward, and the service does not look ahead.
It makes younger holders give way at a level as it reaches that level, and when it finds an
older holder it stops there and leaves a claim; the give-ups it already forced stand, and
nothing the transaction asked for is granted. That is why a refused request is not a no-op
and why the same program decided atomically produces a different trace from its first
conflicting line onward.

The chain of modes the take needs is computed from the transaction's own state before any of
that begins, innermost first, because a cover is what the thing below it requires. It is then
applied in one piece when the last level passes, and printed outermost first, which is the
order a cover and the grant it covers come into existence in.

A retake is the same procedure with its refusal silent. A release and a shut take a subtree
away without leaving anything behind.
"""
from lk import give, hold, keep, mode, name, read, say, wide


def chain_want(book, t, res, m):
    """The effective mode every level of the chain must reach for this take to stand."""
    want = {}
    w = mode.sup(mode.sup(book.asked(t, res), m), book.need(t, res))
    want[res] = w
    cur = res
    par = name.up(cur)
    while par is not None:
        w = mode.sup(book.eff(t, par), mode.cov(w))
        want[par] = w
        cur = par
        par = name.up(cur)
    return want


def take(book, due, ages, t, res, m, out, loud):
    want = chain_want(book, t, res, m)
    for node in name.chain(res):
        goal = want[node]
        if book.eff(t, node) == goal:
            continue
        if not book.clash(t, node, goal):
            continue
        foes = book.foes(t, node, goal)
        if any(ages[u] < ages[t] for u in foes):
            due.claim(t, res, m, node)
            if loud:
                out.append(say.wait(t, res, m))
            return False
        for u in sorted(foes, key=lambda x: ages[x]):
            give.hand(book, due, u, node, out)
    buf = []
    book.raise_ask(t, res, m, buf)
    buf.reverse()
    out.extend(buf)
    due.drop(t, res)
    return True


def release(book, due, t, res, out):
    nodes = set(book.sub(t, res)) | set(due.under(t, res))
    if not nodes:
        return
    crown = book.eff(t, res)
    for node in sorted(nodes, key=name.deep):
        book.erase(t, node)
        due.drop(t, node)
        out.append(say.free(t, node))
    par = name.up(res)
    if par is not None and crown is not None:
        book.retune(t, par, out)


def close(book, due, t, out):
    nodes = set(book.held(t)) | set(due.held(t))
    for node in sorted(nodes, key=name.deep):
        out.append(say.free(t, node))
    book.forget(t)
    due.forget(t)
    out.append(say.shut(t))


def run(text):
    out = []
    book = hold.Book()
    due = keep.Due()
    ages = {}
    lim = 0
    for bits in read.scan(text):
        head = bits[0]
        if head == "lim":
            lim = int(bits[1])
        elif head == "open":
            if bits[1] not in ages:
                ages[bits[1]] = len(ages)
        elif head == "take":
            take(book, due, ages, bits[1], bits[2], bits[3], out, True)
        elif head == "drop":
            release(book, due, bits[1], bits[2], out)
        elif head == "shut":
            close(book, due, bits[1], out)
        keep.settle(book, due, ages, out, take)
        wide.widen(book, due, ages, lim, out)
    return out, book, due, ages
