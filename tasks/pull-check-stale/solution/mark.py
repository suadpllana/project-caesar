def read_mark(path, keep):
    """A read observes the bytes: the digest, or `-` when the path was not there."""
    return ("R", path, keep.digest(path))


def look_mark(path, keep):
    """A look observes presence only, so a rewrite of the same path does not disturb it."""
    return ("L", path, "+" if keep.has(path) else "-")


def pull_mark(name, hold):
    """A pull observes the value, or that the step was dead - never the reason."""
    if hold.dead:
        return ("P", name, "!")
    return ("P", name, hold.value)


def out_mark(path, keep):
    """A successful run observes the bytes it left at its own output path."""
    return ("O", path, keep.digest(path))


def is_pull(m):
    return m[0] == "P"


def flat_holds(m, keep):
    """Whether an observation that needs only the workspace still holds."""
    kind = m[0]
    if kind == "R":
        return keep.digest(m[1]) == m[2]
    if kind == "L":
        return keep.has(m[1]) == (m[2] == "+")
    if kind == "O":
        return keep.digest(m[1]) == m[2]
    return True
