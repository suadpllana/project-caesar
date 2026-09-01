def parse(text):
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        out.append(tuple(s.split()))
    return out
