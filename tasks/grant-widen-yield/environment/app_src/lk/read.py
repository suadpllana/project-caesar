def scan(text):
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if line:
            out.append(tuple(line.split()))
    return out
