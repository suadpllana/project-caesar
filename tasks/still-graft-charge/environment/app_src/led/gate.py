from led import cell, cost, say


def cap(st, name, size):
    cell.line(st, name).cap = size


def put(st, name, lo, hi, size):
    one = cell.line(st, name)
    if one.cap is not None and cost.after(st, name, lo, hi, size) > one.cap:
        say.full(st, name)
        return
    cell.write(st, name, lo, hi, size, st.mint())
