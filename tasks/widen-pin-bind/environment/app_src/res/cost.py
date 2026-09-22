from res import kind


def slot(prog, stands, asked):
    return kind.steps(prog, stands, asked)


def result(prog, gives, expected):
    if expected is None:
        return 0
    if kind.steps(prog, gives, expected) is None:
        return None
    return 0
