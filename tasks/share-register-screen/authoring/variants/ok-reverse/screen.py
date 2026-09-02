from reg import poll

from . import tally, voice


def sweep(st):
    on = set(st.named())
    while True:
        grew = False
        for cid in reversed(st.cos()):
            if cid in on:
                continue
            seats = st.seats(cid)
            board = poll.elect(voice.hands(st, cid, on), seats)
            if tally.carries(tally.held(board, on), seats):
                on.add(cid)
                grew = True
        if not grew:
            return on
