def parse(lines):
    span = 0
    part = 0
    body = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        bits = line.split()
        if bits[0] == "span":
            span = int(bits[1])
        elif bits[0] == "part":
            part = int(bits[1])
        else:
            body.append(line)
    return span, part, body


def load(path):
    with open(path, encoding="utf-8") as f:
        return parse(f.read().splitlines())
