from reg import poll

from . import tally, voice


def _reaches(st, cid, on):
    seats = st.seats(cid)
    board = poll.elect(voice.hands(st, cid, on), seats)
    return tally.carries(tally.held(board, on), seats)


def sweep(st):
    on = set(st.named())
    cos = st.cos()
    while True:
        fresh = [cid for cid in cos if cid not in on and _reaches(st, cid, on)]
        if not fresh:
            return on
        on.update(fresh)
