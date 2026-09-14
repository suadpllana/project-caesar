"""How wide a step is, and how many whole steps the epoch can still fill."""


def width(run, st):
    return st["rank"] * run.micro * run.accum


def steps_left(run, st):
    wide = width(run, st)
    return (run.rows - st["fed"]) // wide if wide else 0


def roll(st):
    st["epoch"] += 1
    st["seen"] = {}
    st["fed"] = 0
