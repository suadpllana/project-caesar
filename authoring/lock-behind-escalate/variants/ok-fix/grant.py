NEWEST = 10 ** 18


class Relation:
    """The wait relation as it stands, closed by iterating to a fixed point over bitsets.

    Nodes are visited in depth-first postorder, so every successor that is not on a cycle is
    finished before the node that waits on it and the iteration settles in a pass or two.
    """

    __slots__ = ("held", "wait", "index", "reach", "hard")

    def __init__(self, held, wait):
        self.held = held
        self.wait = wait
        self.index = {}
        self.reach = None
        self.hard = None

    def bit(self, txn):
        if txn not in self.index:
            self.index[txn] = 1 << len(self.index)
        return self.index[txn]

    def build(self):
        hard_edges = {}
        soft_edges = {}
        for txn in self.wait.waiting():
            seq, tgt, mode = self.wait.req[txn]
            hard_edges[txn] = self.held.blockers(txn, tgt, mode)
            soft_edges[txn] = self.wait.rivals(txn, tgt, mode, seq)
        self.hard = self._fix(hard_edges)
        both = {t: hard_edges[t] | soft_edges[t] for t in hard_edges}
        self.reach = self._fix(both)

    @staticmethod
    def _postorder(edges):
        done = []
        seen = set()
        for root in edges:
            if root in seen:
                continue
            seen.add(root)
            todo = [(root, iter(edges[root]))]
            while todo:
                node, it = todo[-1]
                for nxt in it:
                    if nxt in edges and nxt not in seen:
                        seen.add(nxt)
                        todo.append((nxt, iter(edges[nxt])))
                        break
                else:
                    done.append(node)
                    todo.pop()
        return done

    def _fix(self, edges):
        order = self._postorder(edges)
        reach = {}
        for txn in order:
            mask = 0
            for u in edges[txn]:
                mask |= self.bit(u)
            reach[txn] = mask
        changed = True
        while changed:
            changed = False
            for txn in order:
                mask = reach[txn]
                for u in edges[txn]:
                    mask |= reach.get(u, 0)
                if mask != reach[txn]:
                    reach[txn] = mask
                    changed = True
        return reach

    def depends(self, v, txn):
        if self.reach is None:
            self.build()
        return bool(self.reach.get(v, 0) & self.bit(txn))

    def cyclic(self):
        if self.hard is None:
            self.build()
        return [t for t, mask in self.hard.items() if mask & self.bit(t)]


def admissible(held, wait, txn, tgt, mode, seq, rel=None):
    if held.blockers(txn, tgt, mode):
        return False
    for u in wait.rivals(txn, tgt, mode, seq):
        if rel is None:
            rel = Relation(held, wait)
        if not rel.depends(u, txn):
            return False
    return True
