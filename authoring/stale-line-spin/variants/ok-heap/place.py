import heapq


class Place:
    def __init__(self, launch):
        self.grid = launch.grid
        self.cells = [[None] * launch.slots for _ in range(launch.sms)]
        self.holes = [list(range(launch.slots)) for _ in range(launch.sms)]
        self.count = [launch.slots] * launch.sms
        self.room = [(-launch.slots, s) for s in range(launch.sms)] if launch.slots else []
        heapq.heapify(self.room)
        self.next = 0
        self.out = []

    def leave(self, b):
        self.out.append(b)

    def best(self):
        room, count = self.room, self.count
        while room and -room[0][0] != count[room[0][1]]:
            heapq.heappop(room)
        return room[0][1] if room else None

    def admit(self, blocks, t):
        for b in self.out:
            s = b.sm
            self.cells[s][b.slot] = None
            heapq.heappush(self.holes[s], b.slot)
            self.count[s] += 1
            heapq.heappush(self.room, (-self.count[s], s))
        self.out = []
        got = []
        while self.next < self.grid:
            s = self.best()
            if s is None:
                break
            heapq.heappop(self.room)
            j = heapq.heappop(self.holes[s])
            b = blocks[self.next]
            self.cells[s][j] = b
            b.sm, b.slot, b.at = s, j, t
            self.count[s] -= 1
            if self.count[s]:
                heapq.heappush(self.room, (-self.count[s], s))
            self.next += 1
            got.append(b)
        return got
