# One record per company, in the order the register incorporated them.
#
# A seat is written out under the name of whoever took it, except that every seat the
# list took is written with the marker, whether it was taken by the collapsed hand or by
# a member standing alone. Seats nobody could take are gaps.
from reg import poll

MARK = "*"


def line(st, cid, on, board, got):
    seats = []
    for k in board:
        if k == poll.GAP:
            seats.append(poll.GAP)
        elif k in on or not st.known(k):
            seats.append(MARK)
        else:
            seats.append(k)
    return [cid, 1 if cid in on else 0, got, len(board), seats]
