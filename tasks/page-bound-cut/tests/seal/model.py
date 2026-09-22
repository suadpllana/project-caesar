"""Independent model of the specified page layer.

Written apart from solution/: this one carries parent pointers on the nodes, finds a
boundary by walking up while the node is an extreme child, and measures any page - real or
hypothetical - by building its entry list and adding the parts up.  solution/ carries no
parent pointers, walks a spine recorded during descent, and measures a page from its two
end keys, its entry count and a running length sum.  Agreement between the two is the
evidence that the graded trace follows the contract and not one implementation's habits.
"""

import bisect
import re

HEAD = 8
ENT = 2
KID = 2

KEY = re.compile(r"\A[a-z]{1,10}\Z")


class Bad(Exception):
    pass


def parse(body):
    cap = None
    floor = None
    ops = []
    for num, raw in enumerate(body.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        bits = line.split()
        if bits[0] == "page":
            if cap is not None or len(bits) != 3:
                raise Bad("line %d: bad page line" % num)
            cap = int(bits[1])
            floor = int(bits[2])
            continue
        if cap is None:
            raise Bad("line %d: no page line yet" % num)
        if len(bits) != 2 or bits[0] not in ("put", "del"):
            raise Bad("line %d: bad op" % num)
        if not KEY.match(bits[1]):
            raise Bad("line %d: bad key" % num)
        ops.append((bits[0], bits[1]))
    if cap is None:
        raise Bad("no page line")
    return cap, floor, ops


def common(words):
    """Longest common prefix of a list of strings, scanned across all of them."""
    if not words:
        return ""
    out = words[0]
    for w in words[1:]:
        k = 0
        top = min(len(out), len(w))
        while k < top and out[k] == w[k]:
            k += 1
        out = out[:k]
        if not out:
            break
    return out


def divider(low, high):
    """Shortest string greater than low and not greater than high."""
    k = 0
    top = min(len(low), len(high))
    while k < top and low[k] == high[k]:
        k += 1
    return high[:k + 1]


def measure(ents, kids):
    """Stored bytes of a page holding these entries over this many children."""
    total = HEAD + kids * KID
    if ents:
        pre = len(common(ents))
        total += pre
        for e in ents:
            total += ENT + len(e) - pre
    return total


class Node:
    def __init__(self, pid, leaf):
        self.pid = pid
        self.leaf = leaf
        self.keys = []
        self.kids = []
        self.seps = []
        self.up = None


class Idx:
    def __init__(self, cap, floor):
        self.cap = cap
        self.floor = floor
        self.tab = {}
        self.loose = []
        self.next = 1
        self.root = self.make(True).pid

    # --- page table -------------------------------------------------------
    def make(self, leaf):
        if self.loose:
            pid = min(self.loose)
            self.loose.remove(pid)
        else:
            pid = self.next
            self.next += 1
        node = Node(pid, leaf)
        self.tab[pid] = node
        return node

    def toss(self, pid):
        del self.tab[pid]
        self.loose.append(pid)

    def ents(self, node):
        return node.keys if node.leaf else node.seps

    def size(self, node):
        return measure(self.ents(node), 0 if node.leaf else len(node.kids))

    def where(self, node):
        return self.tab[node.up].kids.index(node.pid)

    # --- navigation -------------------------------------------------------
    def find(self, key):
        node = self.tab[self.root]
        while not node.leaf:
            node = self.tab[node.kids[bisect.bisect_right(node.seps, key)]]
        return node

    def low_end(self, pid):
        node = self.tab[pid]
        while not node.leaf:
            node = self.tab[node.kids[0]]
        return node.keys[0] if node.keys else None

    def high_end(self, pid):
        node = self.tab[pid]
        while not node.leaf:
            node = self.tab[node.kids[-1]]
        return node.keys[-1] if node.keys else None

    def before(self, node):
        """The separator immediately to the left of this node's subtree."""
        while node.up is not None:
            j = self.where(node)
            if j > 0:
                return node.up, j - 1
            node = self.tab[node.up]
        return None

    def after(self, node):
        """The separator immediately to the right of this node's subtree."""
        while node.up is not None:
            j = self.where(node)
            if j < len(self.tab[node.up].seps):
                return node.up, j
            node = self.tab[node.up]
        return None

    # --- the boundary invariant ------------------------------------------
    def mend(self, site, out):
        if site is None:
            return
        pid, idx = site
        node = self.tab[pid]
        if idx >= len(node.seps):
            return
        low = self.high_end(node.kids[idx])
        high = self.low_end(node.kids[idx + 1])
        if low is None or high is None:
            return
        want = divider(low, high)
        if node.seps[idx] != want:
            node.seps[idx] = want
            out.append("bound p%d %d %s" % (pid, idx, want))

    # --- cutting ----------------------------------------------------------
    def above_cost(self, node, sep):
        """What promoting sep adds to the page above, or the cost of a new root."""
        if node.up is None:
            return measure([sep], 2)
        host = self.tab[node.up]
        j = self.where(node)
        grown = host.seps[:j] + [sep] + host.seps[j:]
        return measure(grown, len(host.kids) + 1) - measure(host.seps, len(host.kids))

    def plan(self, node):
        best = None
        if node.leaf:
            keys = node.keys
            n = len(keys)
            for i in range(1, n):
                sep = divider(keys[i - 1], keys[i])
                cost = (max(measure(keys[:i], 0), measure(keys[i:], 0))
                        + self.above_cost(node, sep))
                if best is None or (cost, i) < best[0]:
                    best = ((cost, i), i, sep)
        else:
            seps = node.seps
            n = len(seps)
            m = len(node.kids)
            for i in range(n):
                sep = seps[i]
                cost = (max(measure(seps[:i], i + 1), measure(seps[i + 1:], m - i - 1))
                        + self.above_cost(node, sep))
                if best is None or (cost, i) < best[0]:
                    best = ((cost, i), i, sep)
        return best[1], best[2]

    def cut(self, node, out):
        if node.leaf:
            if len(node.keys) < 2:
                return
            pos, sep = self.plan(node)
            mate = self.make(True)
            mate.keys = node.keys[pos:]
            node.keys = node.keys[:pos]
        else:
            if not node.seps:
                return
            pos, sep = self.plan(node)
            mate = self.make(False)
            mate.kids = node.kids[pos + 1:]
            mate.seps = node.seps[pos + 1:]
            node.kids = node.kids[:pos + 1]
            node.seps = node.seps[:pos]
            for k in mate.kids:
                self.tab[k].up = mate.pid
        out.append("cut p%d p%d %d %s" % (node.pid, mate.pid, pos, sep))
        if node.up is None:
            top = self.make(False)
            top.kids = [node.pid, mate.pid]
            top.seps = [sep]
            node.up = top.pid
            mate.up = top.pid
            self.root = top.pid
            out.append("root p%d" % top.pid)
        else:
            host = self.tab[node.up]
            j = self.where(node)
            host.kids.insert(j + 1, mate.pid)
            host.seps.insert(j, sep)
            mate.up = host.pid
        return

    # --- joining ----------------------------------------------------------
    def pair_size(self, left, right, mid):
        if left.leaf:
            return measure(left.keys + right.keys, 0)
        return measure(left.seps + [mid] + right.seps,
                       len(left.kids) + len(right.kids))

    def fuse(self, host, at, out):
        left = self.tab[host.kids[at]]
        right = self.tab[host.kids[at + 1]]
        if left.leaf:
            left.keys = left.keys + right.keys
        else:
            left.seps = left.seps + [host.seps[at]] + right.seps
            left.kids = left.kids + right.kids
            for k in right.kids:
                self.tab[k].up = left.pid
        del host.seps[at]
        del host.kids[at + 1]
        self.toss(right.pid)
        out.append("join p%d p%d" % (left.pid, right.pid))

    def knit(self, node, out):
        host = self.tab[node.up]
        j = self.where(node)
        if j + 1 < len(host.kids):
            mate = self.tab[host.kids[j + 1]]
            if self.pair_size(node, mate, host.seps[j]) <= self.cap:
                self.fuse(host, j, out)
                return
        if j > 0:
            mate = self.tab[host.kids[j - 1]]
            if self.pair_size(mate, node, host.seps[j - 1]) <= self.cap:
                self.fuse(host, j - 1, out)

    def strip(self, node, out):
        """A page holding nothing leaves the tree, and the page above loses a string."""
        host = self.tab[node.up]
        j = self.where(node)
        last = len(host.kids) - 1
        if 0 < j < last:
            site = (host.pid, j - 1)
        elif j == 0:
            site = self.before(host)
        else:
            site = self.after(host)
        if j > 0:
            del host.seps[j - 1]
        elif host.seps:
            del host.seps[0]
        del host.kids[j]
        self.toss(node.pid)
        out.append("gone p%d" % node.pid)
        if host.kids:
            self.mend(site, out)

    def fold(self, out):
        """While the root is an internal page with one child, that child becomes the root."""
        while True:
            node = self.tab[self.root]
            if node.leaf or len(node.kids) != 1:
                return
            kid = node.kids[0]
            self.toss(self.root)
            self.root = kid
            self.tab[kid].up = None
            out.append("fold p%d" % kid)

    # --- one operation ----------------------------------------------------
    def put(self, key, out):
        leaf = self.find(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i < len(leaf.keys) and leaf.keys[i] == key:
            out.append("dup %s" % key)
            return
        leaf.keys.insert(i, key)
        out.append("add %s p%d" % (key, leaf.pid))
        if len(leaf.keys) > 1:
            if i == 0:
                self.mend(self.before(leaf), out)
            elif i == len(leaf.keys) - 1:
                self.mend(self.after(leaf), out)
        node = leaf
        while node is not None:
            up = node.up
            if self.size(node) > self.cap:
                self.cut(node, out)
            node = None if up is None else self.tab[up]

    def drop(self, key, out):
        leaf = self.find(key)
        i = bisect.bisect_left(leaf.keys, key)
        if i >= len(leaf.keys) or leaf.keys[i] != key:
            out.append("none %s" % key)
            return
        low = i == 0
        high = i == len(leaf.keys) - 1
        del leaf.keys[i]
        out.append("rm %s p%d" % (key, leaf.pid))
        if leaf.keys:
            if low:
                self.mend(self.before(leaf), out)
            elif high:
                self.mend(self.after(leaf), out)
        node = leaf
        while node is not None and node.up is not None:
            up = node.up
            if not (node.keys if node.leaf else node.kids):
                self.strip(node, out)
            elif self.size(node) < self.floor:
                self.knit(node, out)
            node = self.tab[up]
        self.fold(out)


def trace(body):
    cap, floor, ops = parse(body)
    idx = Idx(cap, floor)
    out = []
    for kind, key in ops:
        if kind == "put":
            idx.put(key, out)
        else:
            idx.drop(key, out)
    return out
