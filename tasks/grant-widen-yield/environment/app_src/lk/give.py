def hand(book, due, u, res, out):
    was = book.eff(u, res)
    if was is None:
        return
    book.cut(u, res, out, "give")
    due.claim(u, res, was)
