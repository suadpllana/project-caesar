"""Reference `carry`: the earliest stamp that reaches `b` when `a` emits at `x`.

Not a distance. Every node on the way rewrites what passes through it, and two
of the rewrites are not additive, so a shortest path measured in lag alone is
the wrong object: a longer way round through a lift with a low floor can land
earlier than a short way round through one with a high floor, and which of the
two wins depends on the stamp being asked about. So the answer is a relaxation
over the whole graph for the stamp in hand, run to a fixed point because the
graph has edges that lead back to where they came from.

Two values are tracked per node and they are not the same. `arr` is the
earliest stamp that reaches the node, which is what the caller asked for.
`src` is the earliest stamp the node then puts back on its own out edges,
which is what the relaxation carries onward. They differ at exactly the nodes
whose rewrite is not the identity, and conflating them is how a gather in the
middle of a route stops being a barrier and turns into a wire.

Anything at or above the horizon is discarded rather than delivered, so it
neither arrives nor propagates.
"""


def step(st, n, y):
    g = st.g
    k = g.kind[n]
    if k == "relay":
        return y
    if k == "lift":
        return y if y >= g.par[n] else g.par[n]
    if k == "gather":
        w = g.par[n]
        return (y // w + 1) * w - 1
    return None


def carry(st, a, x, b):
    g = st.g
    if x is None or x >= g.hz:
        return None
    src = {a: x}
    arr = {}
    live = True
    while live:
        live = False
        for u in sorted(src):
            v = src[u]
            for d, lag in g.out[u]:
                y = v + lag
                if y >= g.hz:
                    continue
                if d not in arr or y < arr[d]:
                    arr[d] = y
                    live = True
                e = step(st, d, y)
                if e is None or e >= g.hz:
                    continue
                if d not in src or e < src[d]:
                    src[d] = e
                    live = True
    return arr.get(b)
