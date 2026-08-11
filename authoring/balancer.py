"""Exact integer balancing of a candidate reaction given only its species lists.

A candidate names the species on each side but not their coefficients. Balancing means
finding positive integers x_i such that every element and the total charge cancel. That
is a nullspace computation over the rationals; the result is classified as:

    "unique"     exactly one independent balance, and it can be scaled all-positive
    "none"       no all-positive balance exists (nullspace empty, or forced signs)
    "ambiguous"  two or more independent balances exist
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd

import species as sp


def _nullspace(rows: list[list[Fraction]], ncols: int) -> list[list[Fraction]]:
    """Exact rational nullspace basis of the matrix given as a list of rows."""
    mat = [row[:] for row in rows]
    pivots: list[int] = []
    r = 0
    for c in range(ncols):
        piv = next((i for i in range(r, len(mat)) if mat[i][c] != 0), None)
        if piv is None:
            continue
        mat[r], mat[piv] = mat[piv], mat[r]
        lead = mat[r][c]
        mat[r] = [v / lead for v in mat[r]]
        for i in range(len(mat)):
            if i != r and mat[i][c] != 0:
                factor = mat[i][c]
                mat[i] = [a - factor * b for a, b in zip(mat[i], mat[r])]
        pivots.append(c)
        r += 1
        if r == len(mat):
            break

    free = [c for c in range(ncols) if c not in pivots]
    basis = []
    for f in free:
        vec = [Fraction(0)] * ncols
        vec[f] = Fraction(1)
        for i, pc in enumerate(pivots):
            vec[pc] = -mat[i][f]
        basis.append(vec)
    return basis


def balance(reactants: list[str], products: list[str]) -> tuple[str, dict[str, int], dict[str, int]]:
    """Return (status, reactant_coefs, product_coefs)."""
    order = list(reactants) + list(products)
    signs = [1] * len(reactants) + [-1] * len(products)

    elements = sorted({el for s in order for el in sp.atom_counts(s)})
    rows: list[list[Fraction]] = []
    for el in elements:
        rows.append([Fraction(signs[i] * sp.atom_counts(s).get(el, 0)) for i, s in enumerate(order)])
    rows.append([Fraction(signs[i] * sp.charge_of(s)) for i, s in enumerate(order)])

    basis = _nullspace(rows, len(order))
    if not basis:
        return "none", {}, {}
    if len(basis) > 1:
        return "ambiguous", {}, {}

    vec = basis[0]
    if all(v <= 0 for v in vec):
        vec = [-v for v in vec]
    if any(v <= 0 for v in vec):
        return "none", {}, {}

    denom = 1
    for v in vec:
        denom = denom * v.denominator // gcd(denom, v.denominator)
    ints = [int(v * denom) for v in vec]
    g = 0
    for v in ints:
        g = gcd(g, v)
    ints = [v // g for v in ints]

    rc: dict[str, int] = {}
    pc: dict[str, int] = {}
    for i, s in enumerate(order):
        (rc if i < len(reactants) else pc)[s] = ints[i]
    return "unique", rc, pc
