class Loop(Exception):
    """A pull that reached a step already on the live stack."""

    def __init__(self, chain):
        Exception.__init__(self)
        self.chain = chain


class Stuck(Exception):
    """A step that has already run this round and has since gone stale."""

    def __init__(self, name):
        Exception.__init__(self)
        self.name = name


class Hold:
    """What the engine remembers about one step.

    `seen` is the workspace stamp at which the record was last found to hold. `ran` says
    the step has actually run this round, which is a different fact from having been
    checked: a step that was only checked and has since gone stale runs, a step that ran
    and has since gone stale is `stuck`.
    """

    def __init__(self, name):
        self.name = name
        self.rec = []
        self.value = None
        self.why = None
        self.dead = False
        self.known = False
        self.seen = -1
        self.ran = False


class Board:
    def __init__(self, p):
        self.holds = {}
        for name in p.order:
            self.holds[name] = Hold(name)

    def get(self, name):
        return self.holds[name]

    def open_round(self):
        for h in self.holds.values():
            h.ran = False

    def reset(self, name):
        """Undo a run that was cut short, so the step is as if it had never run."""
        h = self.holds[name]
        h.rec = []
        h.value = None
        h.why = None
        h.dead = False
        h.known = False
        h.seen = -1
