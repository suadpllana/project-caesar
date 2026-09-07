from prog.deck import CLASH


def settle(lot):
    lead = lot[0]
    for c in lot:
        if c != lead:
            return (CLASH, None)
    return lead
