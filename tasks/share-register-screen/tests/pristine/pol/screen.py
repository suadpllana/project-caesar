from reg import poll

from . import tally, voice


def sweep(st):
    on = set(st.named())
    for cid in st.cos():
        if cid in on:
            continue
        seats = st.seats(cid)
        board = poll.elect(voice.hands(st, cid, on), seats)
        if tally.carries(tally.held(board, on), seats):
            on.add(cid)
    return on
