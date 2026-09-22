from res import spec


class State:
    def __init__(self, prog):
        self.prog = prog


def new(prog):
    return State(prog)


def total(state):
    return 2


def ask(state, node):
    return spec.Result("bind", "c", [(0, 1), (1, 0)], [])
