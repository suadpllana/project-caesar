from lk import give, mode, name, say


def widen(book, due, ages, lim, out):
    for t in sorted(ages, key=lambda x: ages[x]):
        near = [r for r in book.held(t) if name.depth(r) < 2]
        for node in sorted(near, key=name.key):
            kids = [r for r in book.held(t) if name.up(r) == node]
            kids += [r for r in due.held(t) if name.up(r) == node]
            if len(kids) <= lim:
                continue
            want = book.eff(t, node)
            for kid in kids:
                want = mode.sup(want, book.eff(t, kid) or due.owed(t, kid))
            for u, um in sorted(book.at(node).items()):
                if u != t and not mode.ok(um, want):
                    give.hand(book, due, u, node, out)
            count = len(kids)
            for kid in sorted(kids, key=name.key):
                for res in book.sub(t, kid):
                    book.cut(t, res, out, "free")
            book.put(t, node, want, out)
            out.append(say.wide(t, node, want, count))
