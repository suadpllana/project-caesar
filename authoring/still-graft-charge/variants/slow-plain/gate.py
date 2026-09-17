from led import cell, cost, say


def cap(st, name, size):
    cell.line(st, name).cap = size


def put(st, name, lo, hi, size):
    one = cell.line(st, name)
    made = cell.write(st, name, lo, hi, size)
    if one.cap is not None and cost.charge(st, name) > one.cap:
        cell.undo(st, name, made)
        say.full(st, name)
        return
    num = st.mint()
    for _c, _old, b in made:
        b.num = num
