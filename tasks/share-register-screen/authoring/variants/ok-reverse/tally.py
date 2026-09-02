# How many of a company's directors the list holds, and whether that is enough.
#
# Once the meeting sees one voter, the seats belong to that voter. Counting seats whose
# taker is on the list is the same answer only while the members stand apart; after the
# collapse no member takes a seat under its own name, so the count has to be of the
# collapsed hand.
from .voice import BLOC


def held(board, on):
    return sum(1 for k in board if k == BLOC)


def carries(got, seats):
    return 2 * got > seats
