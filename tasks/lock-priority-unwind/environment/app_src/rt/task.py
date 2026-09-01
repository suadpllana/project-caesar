RUN = "run"
LOCK = "lock"
UNLOCK = "unlock"
SLEEP = "sleep"


class Task:
    __slots__ = ("id", "base", "start", "prog")

    def __init__(self, tid, base, start, prog):
        self.id = tid
        self.base = base
        self.start = start
        self.prog = prog

    def __repr__(self):
        return "T(%d p=%d @%d)" % (self.id, self.base, self.start)
