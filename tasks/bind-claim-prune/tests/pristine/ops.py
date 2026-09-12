from bind import book, say, wire


def ex(job, w):
    op = w[0]
    if op == "u":
        book.unit(job, w[1])
    elif op == "p":
        book.part(job, int(w[1]), w[2])
    elif op == "g":
        book.give(job, w[1], w[2])
    elif op == "r":
        book.use(job, w[1], w[2])
    elif op == "t":
        book.spare(job, w[1], w[2])
    elif op == "b":
        book.bundle(job, w[1], w[2:])
    elif op == "bulk":
        book.bulk(job, w[1], w[2], int(w[3]), int(w[4]))
    elif op == "root":
        book.root(job, w[1])
    elif op == "hold":
        book.hold(job, w[1], int(w[2]))
    elif op == "link":
        wire.run(job, book.items(job, w[1:]))
    elif op == "at":
        say.at(job, w[1], wire.at(job, w[1]))
    elif op == "img":
        say.img(job, wire.img(job))
