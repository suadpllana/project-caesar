"""Ground-truth species definitions for the reaction-network task.

Each species carries an explicit heavy-atom structure: atoms (element + attached
hydrogen count), bonds with orders, and a formal charge. Molecular formula and
charge are DERIVED from the structure here, so the data the agent receives is
internally consistent except where a conflict is planted deliberately.
"""

from __future__ import annotations

# id -> (name, atoms, bonds, charge)
#   atoms: list of (atom_id, element, n_hydrogens)
#   bonds: list of (atom_id_a, atom_id_b, order)
SPECIES = {
    "S01": (
        "pyruvate",
        [("C1", "C", 3), ("C2", "C", 0), ("O1", "O", 0),
         ("C3", "C", 0), ("O2", "O", 0), ("O3", "O", 0)],
        [("C1", "C2", 1), ("C2", "O1", 2), ("C2", "C3", 1),
         ("C3", "O2", 2), ("C3", "O3", 1)],
        -1,
    ),
    "S02": (
        "acetaldehyde",
        [("C1", "C", 3), ("C2", "C", 1), ("O1", "O", 0)],
        [("C1", "C2", 1), ("C2", "O1", 2)],
        0,
    ),
    "S03": (
        "carbon dioxide",
        [("C1", "C", 0), ("O1", "O", 0), ("O2", "O", 0)],
        [("C1", "O1", 2), ("C1", "O2", 2)],
        0,
    ),
    "S04": (
        "hydrogencarbonate",
        [("C1", "C", 0), ("O1", "O", 0), ("O2", "O", 0), ("O3", "O", 1)],
        [("C1", "O1", 2), ("C1", "O2", 1), ("C1", "O3", 1)],
        -1,
    ),
    "S05": (
        "ethane-1,1-diol",
        [("C1", "C", 3), ("C2", "C", 1), ("O1", "O", 1), ("O2", "O", 1)],
        [("C1", "C2", 1), ("C2", "O1", 1), ("C2", "O2", 1)],
        0,
    ),
    "S06": (
        "3-hydroxybutan-2-one",
        [("C1", "C", 3), ("C2", "C", 0), ("O1", "O", 0),
         ("C3", "C", 1), ("O2", "O", 1), ("C4", "C", 3)],
        [("C1", "C2", 1), ("C2", "O1", 2), ("C2", "C3", 1),
         ("C3", "O2", 1), ("C3", "C4", 1)],
        0,
    ),
    "S07": (
        "lactate",
        [("C1", "C", 3), ("C2", "C", 1), ("O1", "O", 1),
         ("C3", "C", 0), ("O2", "O", 0), ("O3", "O", 0)],
        [("C1", "C2", 1), ("C2", "O1", 1), ("C2", "C3", 1),
         ("C3", "O2", 2), ("C3", "O3", 1)],
        -1,
    ),
    "S08": (
        "acetate",
        [("C1", "C", 3), ("C2", "C", 0), ("O1", "O", 0), ("O2", "O", 0)],
        [("C1", "C2", 1), ("C2", "O1", 2), ("C2", "O2", 1)],
        -1,
    ),
    "S09": (
        "water",
        [("O1", "O", 2)],
        [],
        0,
    ),
    "S10": (
        "hydron",
        [],
        [],
        1,
    ),
    "P1": (
        "4-hydroxy-2-oxopentanoate",
        [("C1", "C", 3), ("C2", "C", 1), ("O1", "O", 1), ("C3", "C", 2),
         ("C4", "C", 0), ("O2", "O", 0), ("C5", "C", 0),
         ("O3", "O", 0), ("O4", "O", 0)],
        [("C1", "C2", 1), ("C2", "O1", 1), ("C2", "C3", 1), ("C3", "C4", 1),
         ("C4", "O2", 2), ("C4", "C5", 1), ("C5", "O3", 2), ("C5", "O4", 1)],
        -1,
    ),
    # Isomer of P1: a straight-chain 2-oxo acid. Distinguished from P1 by its
    # attached-proton pattern (it carries a CH and a CH2).
    "P2": (
        "2-acetyl-2-hydroxypropanoate",
        [("C1", "C", 3), ("C2", "C", 0), ("O1", "O", 0), ("C3", "C", 0),
         ("O2", "O", 1), ("C4", "C", 3), ("C5", "C", 0),
         ("O3", "O", 0), ("O4", "O", 0)],
        [("C1", "C2", 1), ("C2", "O1", 2), ("C2", "C3", 1), ("C3", "O2", 1),
         ("C3", "C4", 1), ("C3", "C5", 1), ("C5", "O3", 2), ("C5", "O4", 1)],
        -1,
    ),
    # Isomer of P1 with the same attached-proton multiset. Its two methyls sit on the
    # same quaternary carbon, so they are equivalent and it shows one carbon signal fewer.
    "P3": (
        "3-hydroxy-3-methyl-2-oxobutanoate",
        [("C1", "C", 3), ("C2", "C", 0), ("O1", "O", 1), ("C3", "C", 3),
         ("C4", "C", 0), ("O2", "O", 0), ("C5", "C", 0),
         ("O3", "O", 0), ("O4", "O", 0)],
        [("C1", "C2", 1), ("C2", "O1", 1), ("C2", "C3", 1), ("C2", "C4", 1),
         ("C4", "O2", 2), ("C4", "C5", 1), ("C5", "O3", 2), ("C5", "O4", 1)],
        -1,
    ),
    "S12": (
        "butane-2,3-dione",
        [("C1", "C", 3), ("C2", "C", 0), ("O1", "O", 0),
         ("C3", "C", 0), ("O2", "O", 0), ("C4", "C", 3)],
        [("C1", "C2", 1), ("C2", "O1", 2), ("C2", "C3", 1),
         ("C3", "O2", 2), ("C3", "C4", 1)],
        0,
    ),
    "S13": (
        "2-hydroxyprop-2-enoate",
        [("C1", "C", 2), ("C2", "C", 0), ("O1", "O", 1),
         ("C3", "C", 0), ("O2", "O", 0), ("O3", "O", 0)],
        [("C1", "C2", 2), ("C2", "O1", 1), ("C2", "C3", 1),
         ("C3", "O2", 2), ("C3", "O3", 1)],
        -1,
    ),
    "S14": (
        "formate",
        [("C1", "C", 1), ("O1", "O", 0), ("O2", "O", 0)],
        [("C1", "O1", 2), ("C1", "O2", 1)],
        -1,
    ),
    # Aldol product of two aldehyde molecules; an isomer of the ketol, and the
    # product of the competing self-condensation route.
    "S16": (
        "3-hydroxybutanal",
        [("C1", "C", 3), ("C2", "C", 1), ("O1", "O", 1),
         ("C3", "C", 2), ("C4", "C", 1), ("O2", "O", 0)],
        [("C1", "C2", 1), ("C2", "O1", 1), ("C2", "C3", 1),
         ("C3", "C4", 1), ("C4", "O2", 2)],
        0,
    ),
    "S15": (
        "hydroxide",
        [("O1", "O", 1)],
        [],
        -1,
    ),
}

ELEMENT_ORDER = ["C", "H", "O"]


def atom_counts(sid: str) -> dict[str, int]:
    """Element counts derived from the structure, hydrogens included."""
    name, atoms, bonds, charge = SPECIES[sid]
    counts: dict[str, int] = {}
    for _aid, el, nh in atoms:
        counts[el] = counts.get(el, 0) + 1
        if nh:
            counts["H"] = counts.get("H", 0) + nh
    if sid == "S10":  # the bare hydron has no heavy atom to hang its H on
        counts["H"] = counts.get("H", 0) + 1
    return counts


def formula(sid: str) -> str:
    """Hill-style formula string derived from the structure, with charge suffix."""
    counts = atom_counts(sid)
    parts = []
    for el in ELEMENT_ORDER:
        n = counts.get(el, 0)
        if n == 1:
            parts.append(el)
        elif n > 1:
            parts.append(f"{el}{n}")
    charge = SPECIES[sid][3]
    text = "".join(parts) if parts else ""
    if charge == 1:
        text += "+"
    elif charge == -1:
        text += "-"
    elif charge:
        text += f"{abs(charge)}{'+' if charge > 0 else '-'}"
    return text


def heavy_atoms(sid: str) -> list[str]:
    return [aid for aid, _el, _nh in SPECIES[sid][1]]


def element_of(sid: str, aid: str) -> str:
    for a, el, _nh in SPECIES[sid][1]:
        if a == aid:
            return el
    raise KeyError(f"{sid}:{aid}")


def charge_of(sid: str) -> int:
    return SPECIES[sid][3]
