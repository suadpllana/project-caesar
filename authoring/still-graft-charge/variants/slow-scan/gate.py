"""The cap, measured against the charge the put would leave behind.

What a put adds is not what it costs. The cells it names may already hold blocks of this
line's own, and where no still is keeping one of those alive it goes when the put lands, so a
put can be the size of the whole cap and still fit. The only way to know is to have the write
stand and then read the line's charge, which is why the write is taken back rather than
predicted, and why a refused put leaves no block and takes no number.
"""
from led import cell, cost, say


def cap(st, name, size):
    cell.line(st, name).cap = size


def put(st, name, lo, hi, size):
    one = cell.line(st, name)
    made, shut = cell.write(st, name, lo, hi, size)
    if one.cap is not None and cost.charge(st, name) > one.cap:
        cell.undo(st, made, shut)
        say.full(st, name)
        return
    num = st.mint()
    for e in made:
        e.blk.num = num
