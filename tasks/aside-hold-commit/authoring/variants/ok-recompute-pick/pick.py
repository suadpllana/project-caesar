from srv import bite, look
from srv.hold import _futures


def _names(text, inert, limit):
    out = []
    i = 0
    n = min(len(text), limit)
    while i < n:
        if text[i:i + 1] == b"{":
            j = text.find(b"}", i + 1)
            if 0 < j < n and not any(inert[i:j + 1]):
                nm = text[i + 1:j]
                if nm and all(97 <= b <= 122 for b in nm):
                    out.append(nm.decode())
                    i = j + 1
                    continue
        i += 1
    return out


def take(st, sent):
    if st.ended:
        vis, inert = look.read(st.raw)
        text, tin, _ = bite.chop(vis, inert, st.stops)
        return tuple(_names(text, tin, len(sent)))
    lists = []
    for future in _futures(st.raw, st.stops):
        vis, inert = look.read(future)
        text, tin, _ = bite.chop(vis, inert, st.stops)
        lists.append(_names(text, tin, len(sent)))
    names = lists[0]
    for lst in lists[1:]:
        n = 0
        while n < len(names) and n < len(lst) and names[n] == lst[n]:
            n += 1
        names = names[:n]
    return tuple(names)
