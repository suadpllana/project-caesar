from .voice import BLOC


def held(board, on):
    return len(board) - sum(1 for k in board if k != BLOC)


def carries(got, seats):
    return got > seats - got
