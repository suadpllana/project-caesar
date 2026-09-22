from lk import give, hold, keep, mode, name, read, say, wide


def chain_want(book, t, res, m):
    want = {}
    for node in name.chain(res):
        goal = m if node == res else mode.cov(m)
        want[node] = mode.sup(book.eff(t, node), goal)
    return want


def take(book, due, ages, t, res, m, out, loud):
    want = chain_want(book, t, res, m)
    row = name.chain(res)
    for node in row:
        for u, um in book.at(node).items():
            if u == t or mode.ok(um, want[node]):
                continue
            if ages[u] < ages[t]:
                due.claim(t, res, m)
                if loud:
                    out.append(say.wait(t, res, m))
                return False
    for node in row:
        foes = [u for u, um in book.at(node).items()
                if u != t and not mode.ok(um, want[node])]
        for u in sorted(foes, key=lambda x: ages[x]):
            give.hand(book, due, u, node, out)
    for node in reversed(row):
        book.put(t, node, want[node], out)
    due.drop(t, res)
    return True


def release(book, due, t, res, out):
    for node in book.sub(t, res):
        book.cut(t, node, out, "free")
    for node in sorted(due.under(t, res), key=name.deep):
        due.drop(t, node)
        out.append(say.free(t, node))


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
        wide.widen(book, due, ages, lim, out)
        keep.settle(book, due, ages, out, take)
    return out, book, due, ages
