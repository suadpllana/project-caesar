def read_mark(path, keep):
    return ("R", path, keep.digest(path))


def look_mark(path, keep):
    return ("R", path, keep.digest(path))


def pull_mark(name, hold):
    if hold.dead:
        return ("P", name, "!")
    return ("P", name, hold.value)


def out_mark(path, keep):
    return None


def is_pull(m):
    return m[0] == "P"


def flat_holds(m, keep):
    kind = m[0]
    if kind == "R":
        return keep.digest(m[1]) == m[2]
    if kind == "L":
        return keep.has(m[1]) == (m[2] == "+")
    if kind == "O":
        return keep.digest(m[1]) == m[2]
    return True
