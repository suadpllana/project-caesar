from bind import card, rch


def firm(bk, c):
    if card.auth(bk, c) is None:
        return False
    rep = bk.held(c)[0]
    for x in rch.span(bk, c):
        if bk.held(x)[0] < rep:
            return False
    return True
