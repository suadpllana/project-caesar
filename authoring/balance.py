"""Balance helpers used while designing the candidate list."""

from __future__ import annotations

import species as sp


def imbalance(reactants: dict[str, int], products: dict[str, int]) -> dict[str, int]:
    """Product-side minus reactant-side, per element plus 'charge'. Empty means balanced."""
    delta: dict[str, int] = {}
    for side, sign in ((reactants, -1), (products, +1)):
        for sid, coef in side.items():
            for el, n in sp.atom_counts(sid).items():
                delta[el] = delta.get(el, 0) + sign * coef * n
            delta["charge"] = delta.get("charge", 0) + sign * coef * sp.charge_of(sid)
    return {k: v for k, v in delta.items() if v}


def show(label: str, reactants: dict[str, int], products: dict[str, int]) -> None:
    d = imbalance(reactants, products)
    left = " + ".join(f"{c if c > 1 else ''}{s}" for s, c in reactants.items())
    right = " + ".join(f"{c if c > 1 else ''}{s}" for s, c in products.items())
    print(f"{label:34s} {left:28s} -> {right:28s} {'BALANCED' if not d else d}")
