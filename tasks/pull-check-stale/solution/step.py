from eng import dig
from eng import mark


def run_step(wake, name):
    """Run one step, building its record as the run makes each observation.

    A run that is cut short by a loop or a stuck below it leaves nothing behind: the hold
    is reset, so the step counts as never having run. A run that dies on its own - a read
    of a path that is not there, or a pull of a dead step - keeps the record it built,
    ending with the observation it died on. That partial record is what brings the step
    back to life later: the absence it recorded is exactly what stops holding when the
    path appears.
    """
    board = wake.board
    wake.out.run(name)
    board.reset(name)
    try:
        return _body(wake, name)
    except Exception:
        board.reset(name)
        raise


def _body(wake, name):
    keep = wake.keep
    st = wake.plan.steps[name]
    hold = wake.board.get(name)
    vals = []
    for code, arg in st.ops:
        if code == "read":
            hold.rec.append(mark.read_mark(arg, keep))
            if not keep.has(arg):
                hold.dead = True
                hold.why = "missing %s" % arg
                break
            vals.append(keep.text(arg))
        elif code == "look":
            hold.rec.append(mark.look_mark(arg, keep))
        elif code == "pull":
            other = wake.up(arg)
            hold.rec.append(mark.pull_mark(arg, other))
            if other.dead:
                hold.dead = True
                hold.why = "via %s" % arg
                break
            vals.append(other.value)
        else:
            hold.value = dig.mix(vals) if arg == "*" else arg
            break
    hold.known = True
    if not hold.dead:
        keep.put(st.out, hold.value)
        hold.rec.append(mark.out_mark(st.out, keep))
    hold.ran = True
    hold.seen = keep.stamp
    return hold
