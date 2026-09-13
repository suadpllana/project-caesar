from pan import grid, say


def pas(p):
    line = grid.note("pass")
    say.seen(int(line.split()[1]) if line else 0)
