from reg import poll

from . import tally, voice


def sweep(st):
    on = set(st.named())
    pending = list(st.cos())
    while pending:
        cid = pending.pop()
        if cid in on:
            continue
        seats = st.seats(cid)
        board = poll.elect(voice.hands(st, cid, on), seats)
        if tally.carries(tally.held(board, on), seats):
            on.add(cid)
            pending = [c for c in st.cos() if c not in on]
    return on
