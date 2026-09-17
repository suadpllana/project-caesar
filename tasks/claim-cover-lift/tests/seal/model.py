"""The sealed model: the claim service written a second time, from the rules alone.

It shares no code with the reference under `solution/` and is organised the other way round.
Holdings are kept job-major, one string of mode letters per job and node in the order they were
taken, and the jobs of a box are the index the family test reads; the reference keeps them
node-major with a per box tally. Blockers are found from the box's member jobs here and from
the node's holder map there. Stuck sets are found with Tarjan's strongly connected components
over the part of the waits-for relation reachable from the job that has just started waiting;
the reference intersects a forward walk with a backward one.

The rules, in the order the engine applies them:

  1  two modes conflict when at least one of them is w
  2  a hold is a list of acquires; take adds one, drop removes the most recent one on that node
  3  the family of a node is the node, its box, and its slots
  4  a request is granted at once when the job already covers it on that node or on its box
  5  otherwise it is granted when nothing in its family blocks it: a conflicting claim of
     another job, or a conflicting request of another job with a smaller sequence number
  6  a blocked request waits and takes the next sequence number
  7  a slot request by a job holding four or more slots of that box, and no covering claim on
     it, becomes a request for the box, in w when the request or any of those claims is w
  8  a granted lifted request frees the job's slot claims in that box in slot order and then
     grants the request that caused it
  9  after anything a job holds changes, the smallest numbered grantable request is granted,
     and that repeats until none is grantable
 10  with the sweep settled, while a job lies on a cycle of the waits-for relation, the job on
     any cycle with the fewest acquires is stopped, ties to the largest job number
 11  a job ignores every line naming it while its own request is waiting, after it has
     ended, and after it has been stopped
 12  end frees every acquire in node order and then says done
 13  show lists the jobs holding a node in job order with their acquires as sorted letters
"""
import bisect

FLOOR = 4


def boxof(node):
    cut = node.find(":")
    return node if cut < 0 else node[:cut]


def nkey(node):
    box = boxof(node)
    if box == node:
        return (int(node[1:]), 0, 0)
    return (int(box[1:]), 1, int(node[node.find(":") + 2:]))


def jkey(job):
    return int(job[1:])


def clash(one, two):
    return one == "w" or two == "w"


class Ask:
    def __init__(self, seq, job, node, mode, trig):
        self.seq = seq
        self.job = job
        self.node = node
        self.mode = mode
        self.trig = trig


class Engine:
    def __init__(self):
        self.out = []
        self.got = {}           # job -> node -> letters, in the order taken
        self.jobs = {}          # node -> set of jobs holding it
        self.kin = {}           # box -> job -> [slot acquires in r, slot acquires in w]
        self.asks = {}          # seq -> Ask
        self.queue = {}         # box -> sorted list of seqs
        self.mine = {}          # job -> Ask
        self.seq = 0
        self.over = set()

    # --- what a job holds -------------------------------------------------------------

    def letters(self, job, node):
        return self.got.get(job, {}).get(node, "")

    def put(self, job, node, mode):
        mine = self.got.setdefault(job, {})
        mine[node] = mine.get(node, "") + mode
        self.jobs.setdefault(node, set()).add(job)
        box = boxof(node)
        if box != node:
            tal = self.kin.setdefault(box, {}).setdefault(job, [0, 0])
            tal[1 if mode == "w" else 0] += 1

    def take_off(self, job, node):
        mine = self.got.get(job, {})
        text = mine.get(node, "")
        if not text:
            return None
        mode = text[-1]
        text = text[:-1]
        if text:
            mine[node] = text
        else:
            mine.pop(node)
            self.jobs[node].discard(job)
            if not self.jobs[node]:
                self.jobs.pop(node)
        box = boxof(node)
        if box != node:
            tal = self.kin[box][job]
            tal[1 if mode == "w" else 0] -= 1
            if tal == [0, 0]:
                del self.kin[box][job]
                if not self.kin[box]:
                    del self.kin[box]
        return mode

    def acquires(self, job):
        return sum(len(text) for text in self.got.get(job, {}).values())

    def free_all(self, job):
        hit = set()
        for node in sorted(self.got.get(job, {}), key=nkey):
            while self.letters(job, node):
                self.take_off(job, node)
                self.out.append("free %s %s" % (job, node))
            hit.add(boxof(node))
        return hit

    # --- what may be granted ----------------------------------------------------------

    def covers(self, job, node, mode):
        for held in (node, boxof(node)):
            text = self.letters(job, held)
            if text and (mode == "r" or "w" in text):
                return True
        return False

    def blocked_by(self, job, node, mode, seq):
        out = set()
        box = boxof(node)
        for other in self.jobs.get(node, ()):
            if other != job and any(clash(mode, m) for m in self.letters(other, node)):
                out.add(other)
        if box == node:
            for other, tal in self.kin.get(box, {}).items():
                if other != job and (mode == "w" or tal[1] > 0):
                    out.add(other)
        else:
            for other in self.jobs.get(box, ()):
                if other != job and any(clash(mode, m) for m in self.letters(other, box)):
                    out.add(other)
        for other_seq in self.queue.get(box, ()):
            if other_seq >= seq:
                break
            ask = self.asks[other_seq]
            if ask.job == job or not clash(mode, ask.mode):
                continue
            if box == node or ask.node == node or ask.node == box:
                out.add(ask.job)
        return out

    # --- the line ---------------------------------------------------------------------

    def park(self, job, node, mode, trig):
        self.seq += 1
        ask = Ask(self.seq, job, node, mode, trig)
        self.asks[ask.seq] = ask
        bisect.insort(self.queue.setdefault(boxof(node), []), ask.seq)
        self.mine[job] = ask
        self.out.append("wait %s %s %s" % (job, node, mode))

    def unpark(self, ask):
        self.asks.pop(ask.seq, None)
        row = self.queue.get(boxof(ask.node))
        if row:
            spot = bisect.bisect_left(row, ask.seq)
            if spot < len(row) and row[spot] == ask.seq:
                row.pop(spot)
        if self.mine.get(ask.job) is ask:
            del self.mine[ask.job]

    def hand(self, job, node, mode, trig):
        self.put(job, node, mode)
        self.out.append("grant %s %s %s" % (job, node, mode))
        hit = {boxof(node)}
        if trig is not None:
            box = node
            for slot in sorted([n for n in self.got.get(job, {}) if boxof(n) == box and n != box],
                               key=nkey):
                while self.letters(job, slot):
                    self.take_off(job, slot)
                    self.out.append("free %s %s" % (job, slot))
            self.put(job, trig[0], trig[1])
            self.out.append("grant %s %s %s" % (job, trig[0], trig[1]))
        return hit

    def ready(self, box):
        for seq in list(self.queue.get(box, ())):
            ask = self.asks[seq]
            if not self.blocked_by(ask.job, ask.node, ask.mode, seq):
                return ask
        return None

    def sweep(self, hit):
        warm = set(hit)
        while warm:
            pick = None
            for box in sorted(warm):
                ask = self.ready(box)
                if ask is None:
                    warm.discard(box)
                elif pick is None or ask.seq < pick.seq:
                    pick = ask
            if pick is None:
                return
            self.unpark(pick)
            warm.add(boxof(pick.node))
            warm |= self.hand(pick.job, pick.node, pick.mode, pick.trig)

    # --- jobs waiting for each other --------------------------------------------------

    def edges(self, job):
        ask = self.mine.get(job)
        if ask is None:
            return set()
        return self.blocked_by(job, ask.node, ask.mode, ask.seq)

    def tangle(self, job):
        """Every job on a cycle through this one, by Tarjan over the reachable subgraph."""
        if job not in self.mine:
            return set()
        index, low, on, stack, order, rings = {}, {}, set(), [], [], []
        work = [(job, iter(sorted(self.edges(job))))]
        index[job] = low[job] = 0
        order.append(job)
        stack.append(job)
        on.add(job)
        step = 1
        while work:
            top, kids = work[-1]
            moved = False
            for kid in kids:
                if kid not in index:
                    index[kid] = low[kid] = step
                    step += 1
                    stack.append(kid)
                    on.add(kid)
                    work.append((kid, iter(sorted(self.edges(kid)))))
                    moved = True
                    break
                if kid in on:
                    low[top] = min(low[top], index[kid])
            if moved:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[top])
            if low[top] == index[top]:
                part = []
                while True:
                    one = stack.pop()
                    on.discard(one)
                    part.append(one)
                    if one == top:
                        break
                if len(part) > 1:
                    rings.append(set(part))
        for part in rings:
            if job in part:
                return part
        return set()

    def cut(self, job):
        self.out.append("stop %s" % job)
        self.over.add(job)
        ask = self.mine.get(job)
        hit = set()
        if ask is not None:
            self.unpark(ask)
            hit.add(boxof(ask.node))
        return hit | self.free_all(job)

    def settle(self, job):
        while True:
            ring = self.tangle(job)
            if not ring:
                return
            worst = min(ring, key=lambda one: (self.acquires(one), -jkey(one)))
            self.sweep(self.cut(worst))

    # --- the operations ---------------------------------------------------------------

    def take(self, job, node, mode):
        if job in self.over or job in self.mine:
            return
        if self.covers(job, node, mode):
            self.put(job, node, mode)
            self.out.append("grant %s %s %s" % (job, node, mode))
            return
        box = boxof(node)
        trig = None
        if box != node:
            held = [n for n in self.got.get(job, {}) if boxof(n) == box and n != box]
            if len(held) >= FLOOR:
                wet = mode == "w" or any("w" in self.letters(job, n) for n in held)
                mode, trig, node = ("w" if wet else "r"), (node, mode), box
                self.out.append("lift %s %s %s" % (job, node, mode))
        if self.blocked_by(job, node, mode, self.seq + 1):
            self.park(job, node, mode, trig)
            self.settle(job)
        else:
            self.sweep(self.hand(job, node, mode, trig))

    def drop(self, job, node):
        if job in self.over or job in self.mine:
            return
        if self.take_off(job, node) is not None:
            self.out.append("free %s %s" % (job, node))
            self.sweep({boxof(node)})

    def end(self, job):
        if job in self.over or job in self.mine:
            return
        hit = self.free_all(job)
        self.out.append("done %s" % job)
        self.over.add(job)
        self.sweep(hit)

    def show(self, node):
        row = [node]
        for job in sorted(self.jobs.get(node, ()), key=jkey):
            row.append(job)
            row.append("".join(sorted(self.letters(job, node))))
        self.out.append("at %s" % " ".join(row))


def expect(lines):
    eng = Engine()
    for raw in lines:
        w = raw.split()
        if not w:
            continue
        if w[0] == "take":
            eng.take(w[1], w[2], w[3])
        elif w[0] == "drop":
            eng.drop(w[1], w[2])
        elif w[0] == "end":
            eng.end(w[1])
        elif w[0] == "show":
            eng.show(w[1])
        elif w[0] == "fill":
            for i in range(1, int(w[3]) + 1):
                eng.take(w[1], "%s:s%d" % (w[2], i), w[4])
    return eng.out
