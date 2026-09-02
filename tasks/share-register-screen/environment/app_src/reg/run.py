from . import poll, site
from pol import note, screen, tally, voice


def drive(bk):
    st = site.Site(bk)
    on = screen.sweep(st)
    rows = []
    for cid in st.cos():
        hands = voice.hands(st, cid, on)
        board = poll.elect(hands, st.seats(cid))
        got = tally.held(board, on)
        rows.append(note.line(st, cid, on, board, got))
    return rows
