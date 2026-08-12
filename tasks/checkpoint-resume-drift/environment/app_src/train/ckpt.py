HOLD = ("model", "opt")


def pack_state(cx):
    out = []
    for nm in HOLD:
        v = list(getattr(cx, nm).snap())
        out.append(len(v))
        out.extend(v)
    return out


def unpack_state(cx, vec):
    i = 0
    for nm in HOLD:
        if i >= len(vec):
            break
        n = vec[i]
        getattr(cx, nm).rest(vec[i + 1: i + 1 + n])
        i += 1 + n
