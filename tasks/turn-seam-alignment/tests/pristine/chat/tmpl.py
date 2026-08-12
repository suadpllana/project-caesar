U = "\x01"
B = "\x02"
T = "\x03"
E = "\x04"


def block(role, text):
    if role == "u":
        return U + text + E
    if role == "t":
        return T + text + E
    if text.endswith(E):
        return B + text
    return B + text + E


def render(msgs, open_bot):
    out = []
    for r, t in msgs:
        out.append(block(r, t))
    if open_bot:
        out.append(B)
    return "".join(out)
