GAP = "-"


def elect(hands, seats):
    got = {}
    live = sorted(k for k, v in hands.items() if v > 0)
    for k in live:
        got[k] = 0
    out = []
    for _ in range(seats):
        top = None
        for k in live:
            if top is None:
                top = k
                continue
            if hands[k] * (got[top] + 1) > hands[top] * (got[k] + 1):
                top = k
        if top is None:
            out.append(GAP)
        else:
            got[top] += 1
            out.append(top)
    return out
