from scr import pin, grp


def kept(before, after):
    """Map before-index -> after-index for every line the pinned script keeps."""
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out


def raised(line, before, after):
    for chunk in grp.spans(before, after):
        if line in chunk:
            return True
    return False
