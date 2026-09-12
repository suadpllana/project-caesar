import heapq

from bind import say


class Row:
    def __init__(self, job, name):
        self.name = name
        self.mem = job.bundles.get(name, ())
        self.idx = {}
        for pos, who in enumerate(self.mem):
            u = job.units.get(who)
            if u is None:
                continue
            for p in u.parts:
                for nm, strong in p.gives:
                    if not strong:
                        continue
                    row = self.idx.get(nm)
                    if row is None:
                        self.idx[nm] = [pos]
                    elif row[-1] != pos:
                        row.append(pos)
        self.heap = []
        self.taken = set()
        self.at = {}
        self.seen = 0


def offer(row, nm):
    run = row.idx.get(nm)
    if not run:
        return
    i = row.at.get(nm, 0)
    while i < len(run) and run[i] in row.taken:
        i += 1
    row.at[nm] = i
    if i < len(run):
        heapq.heappush(row.heap, (run[i], nm))


def ahead(st, row):
    while row.seen < len(st.names.fresh):
        offer(row, st.names.fresh[row.seen])
        row.seen += 1
    while row.heap:
        pos, nm = row.heap[0]
        if pos in row.taken:
            heapq.heappop(row.heap)
            offer(row, nm)
            continue
        if nm not in st.names.want:
            heapq.heappop(row.heap)
            continue
        return pos
    return None


def run(st, bundles):
    board = [Row(st.job, b) for b in bundles]
    while True:
        moved = False
        for row in board:
            while True:
                pos = ahead(st, row)
                if pos is None:
                    break
                row.taken.add(pos)
                who = row.mem[pos]
                if who in st.keep.loaded:
                    continue
                say.take(st.job, row.name, who)
                st.load(who, False)
                moved = True
        if not moved:
            return
