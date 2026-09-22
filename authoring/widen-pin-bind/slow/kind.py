"""The rise graph. `steps` is the only thing anyone asks it for.

A kind rises to another when a chain of declared `rise` edges leads from the first to the
second, and the number the binder wants is the length of the shortest such chain. Two chains
of different lengths between the same pair are ordinary in a declaration set that has grown,
and the shorter one is the answer: the cost of a slot is how far the argument had to travel,
not how far some walk of the graph happened to go.
"""
from collections import deque


def steps(prog, a, b):
    """Shortest number of rise edges from `a` up to `b`, 0 for the same kind, None if none."""
    if a == b:
        return 0
    seen = {a}
    queue = deque([(a, 0)])
    while queue:
        cur, far = queue.popleft()
        for nxt in prog.ups.get(cur, ()):
            if nxt == b:
                return far + 1
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, far + 1))
    return None
