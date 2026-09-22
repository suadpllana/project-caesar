from dbg.image import Inl


def row_at(img, addr):
    f = img.fn_at(addr)
    found = None
    for r in img.rows:
        if f.lo <= r.at <= addr:
            found = r
    return found


def line_at(img, addr):
    r = row_at(img, addr)
    return r.line if r else 0


def scopes(img, addr):
    out = [img.fn_at(addr)]
    for i in img.inls:
        if i.lo <= addr <= i.hi:
            out.append(i)
    return out


def label(s):
    return s.fn.name if isinstance(s, Inl) else s.name


def show(img, pc, stack, hid):
    out = []
    for addr in [pc] + stack[::-1]:
        ch = scopes(img, addr)
        for k in range(len(ch) - 1, -1, -1):
            line = ch[k + 1].call if k + 1 < len(ch) else line_at(img, addr)
            out.append((label(ch[k]), line))
    return out
