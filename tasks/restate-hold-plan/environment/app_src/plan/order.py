from plan.span import ends


def when(pp, row):
    return ends(pp, row[1], row[2]), pp.pos[row[1]]


def order(pp, rows):
    runs = sorted((row for row in rows if row[0] != "hold"), key=lambda row: when(pp, row))
    holds = sorted((row for row in rows if row[0] == "hold"), key=lambda row: when(pp, row))
    return runs + holds
