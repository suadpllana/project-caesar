from prog.deck import CLASH


def settle(cands):
    head = cands[0]
    for c in cands:
        if c != head:
            return (CLASH, None)
    return head
