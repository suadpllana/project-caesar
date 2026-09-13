from pan import grid, say


def top(p):
    line = grid.note("top")
    say.top(int(line.split()[1]) if line else p.top)


def tall(p):
    line = grid.note("tall")
    say.tall(int(line.split()[1]) if line else 0)


def face(p):
    line = grid.note("face")
    if line and line != "face none":
        field = line.split()
        say.face(field[1], int(field[2]))
        return
    if line or not p.rows:
        say.bare()
        return
    say.face(p.rows[0].rid, 0)
