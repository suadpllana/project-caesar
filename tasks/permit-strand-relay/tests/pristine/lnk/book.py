WINF = 40
WINL = 120
LAG = 3
THR = 20
IDLE = 7
FLOOR = 12
MINB = 5
LINK = -1


class Book(object):
    def __init__(self, feeds):
        self.snt = {}
        self.tkn = {}
        self.park = {}
        self.last = {}
        self.shut = {}
        self.pub = {LINK: WINL}
        self.lsnt = 0
        self.ltkn = 0
        for fd in sorted(feeds):
            self.arm(fd, 0)

    def arm(self, fd, t):
        self.snt[fd] = 0
        self.tkn[fd] = 0
        self.park[fd] = []
        self.last[fd] = t
        self.shut[fd] = None
        self.pub[fd] = WINF

    def up(self, fd):
        return self.shut.get(fd, 0) is None

    def open(self):
        return [fd for fd in sorted(self.shut) if self.shut[fd] is None]

    def held(self, fd):
        return sum(r for _, r in self.park.get(fd, []))

    def charge(self, fd, rows):
        self.snt[fd] = self.snt[fd] + rows
        self.lsnt = self.lsnt + rows

    def bill(self, rows):
        self.lsnt = self.lsnt + rows

    def stow(self, t, fd, rows):
        self.park[fd].append((t, rows))
        self.last[fd] = t

    def draw(self, fd):
        if not self.park.get(fd):
            return 0
        _, rows = self.park[fd].pop(0)
        self.tkn[fd] = self.tkn[fd] + rows
        self.ltkn = self.ltkn + rows
        return rows

    def close(self, t, fd):
        rows = self.held(fd)
        self.park[fd] = []
        self.shut[fd] = t
        self.pub.pop(fd, None)
        return rows
