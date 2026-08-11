"""Topological equivalence classes of atoms, by iterative colour refinement.

Two atoms fall in the same class when no walk from one can be distinguished from a
walk from the other. For the small molecules in this network the refinement is exact,
so the number of carbon classes is the number of distinct carbon resonances.
"""

from __future__ import annotations

import species as sp


def classes(sid: str) -> dict[str, int]:
    """atom_id -> class index, stable under relabelling."""
    _name, atoms, bonds, _charge = sp.SPECIES[sid]
    ids = [a for a, _e, _h in atoms]
    adj: dict[str, list[tuple[str, int]]] = {a: [] for a in ids}
    for x, y, order in bonds:
        adj[x].append((y, order))
        adj[y].append((x, order))

    colour = {a: (el, nh) for a, el, nh in atoms}
    labels = {a: hash(colour[a]) for a in ids}
    for _ in range(len(ids) + 1):
        new = {}
        for a in ids:
            sig = (colour[a], tuple(sorted((order, labels[n]) for n, order in adj[a])))
            new[a] = sig
        # compress signatures to small ints so the next round compares structure, not depth
        ordered = sorted(set(new.values()), key=repr)
        index = {s: i for i, s in enumerate(ordered)}
        nxt = {a: index[new[a]] for a in ids}
        if nxt == labels:
            break
        labels = nxt

    ordered = sorted(set(labels.values()))
    remap = {c: i for i, c in enumerate(ordered)}
    return {a: remap[labels[a]] for a in ids}


def carbon_signature(sid: str) -> tuple[int, tuple[int, ...]]:
    """(number of distinct carbon classes, sorted attached-hydrogen counts per class)."""
    cls = classes(sid)
    seen: dict[int, int] = {}
    for aid, el, nh in sp.SPECIES[sid][1]:
        if el != "C":
            continue
        seen.setdefault(cls[aid], nh)
    return len(seen), tuple(sorted(seen.values()))
