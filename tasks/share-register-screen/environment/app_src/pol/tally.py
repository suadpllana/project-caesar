def held(board, on):
    return sum(1 for k in board if k in on)


def carries(got, seats):
    return 2 * got > seats
