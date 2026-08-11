"""Canonical atom map for a balanced reaction.

An atom map pairs every heavy atom on the reactant side with a heavy atom of the same
element on the product side. Among all such pairings the chemically meaningful one keeps
as much of the bonding as possible, so the map is chosen by:

  1. maximise the number of bonds that survive - a bond survives when the two mapped
     partners are bonded on the other side AT THE SAME BOND ORDER;
  2. break ties by taking the lexicographically smallest sorted list of pairs.

Rule 2 is what makes the answer single-valued where a molecule is symmetric, for example
the two hydroxyls of a gem-diol or the two oxygens of carbon dioxide.
"""

from __future__ import annotations

from itertools import permutations

import species as sp


def side_atoms(coefs: dict[str, int]) -> list[tuple[str, int, str, str]]:
    """(species, instance, atom, element) for every heavy atom on one side."""
    out = []
    for sid in sorted(coefs):
        for inst in range(1, coefs[sid] + 1):
            for aid, el, _h in sp.SPECIES[sid][1]:
                out.append((sid, inst, aid, el))
    return out


def side_bonds(coefs: dict[str, int]) -> set[tuple[tuple, tuple, int]]:
    bonds = set()
    for sid in sorted(coefs):
        for inst in range(1, coefs[sid] + 1):
            for x, y, order in sp.SPECIES[sid][2]:
                a, b = (sid, inst, x), (sid, inst, y)
                bonds.add((min(a, b), max(a, b), order))
    return bonds


def ref(node) -> str:
    sid, inst, aid = node
    return f"{sid}#{inst}:{aid}"


def canonical_map(reactants: dict[str, int], products: dict[str, int]):
    left, right = side_atoms(reactants), side_atoms(products)
    lb, rb = side_bonds(reactants), side_bonds(products)

    by_element_left: dict[str, list] = {}
    by_element_right: dict[str, list] = {}
    for sid, inst, aid, el in left:
        by_element_left.setdefault(el, []).append((sid, inst, aid))
    for sid, inst, aid, el in right:
        by_element_right.setdefault(el, []).append((sid, inst, aid))
    assert {e: len(v) for e, v in by_element_left.items()} == \
           {e: len(v) for e, v in by_element_right.items()}, "element counts differ"

    elements = sorted(by_element_left)
    best_score, best_pairs = -1, None
    choices = [list(permutations(by_element_right[el])) for el in elements]

    def walk(i, mapping):
        nonlocal best_score, best_pairs
        if i == len(elements):
            score = 0
            for a, b, order in lb:
                ma, mb = mapping[a], mapping[b]
                if (min(ma, mb), max(ma, mb), order) in rb:
                    score += 1
            pairs = sorted([ref(k), ref(v)] for k, v in mapping.items())
            if score > best_score or (score == best_score and pairs < best_pairs):
                best_score, best_pairs = score, pairs
            return
        el = elements[i]
        for perm in choices[i]:
            nxt = dict(mapping)
            nxt.update(dict(zip(by_element_left[el], perm)))
            walk(i + 1, nxt)

    walk(0, {})
    return best_score, best_pairs
