"""The widen rule: a transaction that holds too much below one node holds the node instead.

The threshold is read against grants, which move in both directions while a program runs -
giving way takes them off a transaction and a retake puts them back - so the decision cannot
be settled when the grants are first taken and a transaction can cross the line on a line
that took nothing of its own.

Widening does not make anyone give way. It is the service tidying its own table, so it fires
only where the mode it needs is already compatible with every other holder at the node, and a
node another transaction is sitting on simply stays fragmented.

The sweep is deepest level first because widening keys into a block can be what takes a
transaction over the threshold in blocks at the store, and it repeats until a round changes
nothing. The pairs it looks at are the ones whose child count moved and the ones sitting on a
node whose holder set moved; every other pair would decide exactly as it decided last time.
"""
from lk import mode, name, say


def pairs(book, lim):
    """The pairs that could decide differently from last time, above the threshold."""
    seen = set(book.bump)
    book.bump = set()
    for res in book.stir:
        for t in list(book.carriers(res)):
            seen.add((t, res))
    book.stir = set()
    return [p for p in seen if len(book.kids(p[0], p[1])) > lim]


def widen(book, due, ages, lim, out):
    pend = pairs(book, lim)
    while pend:
        pend.sort(key=lambda p: (-name.depth(p[1]), ages.get(p[0], 0), name.key(p[1])))
        for t, node in pend:
            if t not in ages:
                continue
            kids = book.kids(t, node)
            if len(kids) <= lim:
                continue
            want = book.asked(t, node)
            for kid in kids:
                want = mode.sup(want, book.eff(t, kid))
            if book.clash(t, node, want):
                continue
            count = len(kids)
            gone = []
            for kid in sorted(kids, key=name.key):
                gone.extend(book.sub(t, kid))
            gone.sort(key=name.deep)
            for res in gone:
                book.erase(t, res)
                out.append(say.free(t, res))
            before = book.eff(t, node)
            buf = []
            book.set_ask(t, node, want, buf)
            if buf and book.eff(t, node) != before:
                buf.pop(0)
            out.append(say.wide(t, node, want, count))
            out.extend(buf)
        pend = pairs(book, lim)
