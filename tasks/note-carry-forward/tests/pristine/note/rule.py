from scr import grp, pin


def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out


def inside(line, before, after):
    for chunk in grp.spans(before, after):
        if line in chunk:
            return True
    return False


def should_raise(inside_now, inside_before):
    return inside_now or inside_before
