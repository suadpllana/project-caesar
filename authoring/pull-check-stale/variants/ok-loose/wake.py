from eng import mark
from eng.hold import Loop, Stuck
from eng.step import run_step


class Wake:
    """Bringing steps up to date.

    Three things decide what happens to a request, and they are checked in this order.
    A step already on the live stack is a loop, and the chain runs from where that step
    first appears. A step whose verdict was taken at the stamp the workspace still
    carries needs nothing: nothing has changed since, so the verdict still holds - that
    is what keeps the diamond programs linear. Otherwise the record is walked in the
    order the run made it, stopping at the first observation that no longer holds;
    walking a pull observation means bringing that step up to date, so the walk is what
    runs steps, and observations past the first failure are neither checked nor run.

    Only then does the record's failure mean anything: a step that has merely been
    checked this round runs, a step that has already run this round is `stuck`.
    """

    def __init__(self, p, keep, board, out):
        self.plan = p
        self.keep = keep
        self.board = board
        self.out = out
        self.path = []

    def open_round(self):
        self.board.open_round()

    def request(self, name):
        self.path = []
        try:
            hold = self.up(name)
        except Loop as exc:
            self.out.loop(exc.chain)
            return
        except Stuck as exc:
            self.out.stuck(exc.name)
            return
        if hold.dead:
            self.out.err(name, hold.why)
        else:
            self.out.ok(name, hold.value)

    def up(self, name):
        if name in self.path:
            i = self.path.index(name)
            raise Loop(self.path[i:] + [name])
        hold = self.board.get(name)
        if hold.known and hold.seen == self.keep.stamp:
            return hold
        self.path.append(name)
        try:
            if hold.known:
                if self.sound(hold):
                    hold.seen = self.keep.stamp
                    return hold
                if hold.ran:
                    raise Stuck(name)
            return run_step(self, name)
        finally:
            self.path.pop()

    def sound(self, hold):
        for m in hold.rec:
            if mark.is_pull(m):
                other = self.up(m["at"])
                if m["gone"]:
                    if not other.dead:
                        return False
                elif other.dead or other.value != m["was"]:
                    return False
            elif not mark.flat_holds(m, self.keep):
                return False
        return True
