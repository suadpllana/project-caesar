"""How many whole steps the epoch still holds, counted instead of compared."""


def width(run, st):
    return st["rank"] * run.micro * run.accum


def left_in_epoch(run, st):
    wide = width(run, st)
    if wide <= 0:
        return 0
    return (run.rows - st["seen"]) // wide


def roll(st):
    st["epoch"] += 1
    st["seen"] = 0
