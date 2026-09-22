from eng import dig
from eng import mark


def run_step(wake, name):
    keep = wake.keep
    board = wake.board
    st = wake.plan.steps[name]
    hold = board.get(name)
    wake.out.run(name)
    hold.rec = []
    hold.value = None
    hold.why = None
    hold.dead = False
    hold.known = False
    vals = []
    for code, arg in st.ops:
        if code == "read":
            if not keep.has(arg):
                hold.rec = []
                hold.dead = True
                hold.why = "missing %s" % arg
                break
            hold.rec.append(mark.read_mark(arg, keep))
            vals.append(keep.text(arg))
        elif code == "look":
            hold.rec.append(mark.look_mark(arg, keep))
        elif code == "pull":
            other = wake.up(arg)
            hold.rec.append(mark.pull_mark(arg, other))
            if other.dead:
                hold.dead = True
                hold.why = other.why
                break
            vals.append(other.value)
        else:
            hold.value = dig.mix(vals) if arg == "*" else arg
            break
    hold.known = True
    if not hold.dead:
        keep.put(st.out, hold.value)
        m = mark.out_mark(st.out, keep)
        if m is not None:
            hold.rec.append(m)
    board.settle(name)
    return hold
