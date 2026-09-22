import heapq


class Page:
    def __init__(self, pid, leaf):
        self.pid = pid
        self.leaf = leaf
        self.keys = []
        self.kids = []
        self.seps = []


class Tree:
    def __init__(self, cap, floor):
        self.cap = cap
        self.floor = floor
        self.pages = {}
        self.spare = []
        self.nxt = 1
        self.root = self.grab(True).pid

    def grab(self, leaf):
        if self.spare:
            pid = heapq.heappop(self.spare)
        else:
            pid = self.nxt
            self.nxt += 1
        page = Page(pid, leaf)
        self.pages[pid] = page
        return page

    def drop(self, pid):
        del self.pages[pid]
        heapq.heappush(self.spare, pid)

    def at(self, pid):
        return self.pages[pid]
