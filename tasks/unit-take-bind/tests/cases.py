"""Enumerated programs, one per graded decision plus the must-still-work side of each fence.

Generated programs cover combinations and stop a submission fitting the shipped examples; these
name the decisions, so a failure says which rule was read wrongly rather than only that something
differs. Every entry is checked against `gt.json`, frozen before the verifier was written.
"""

CASES = {
    # --- rank 0: a unit's own declarations, and that they outrank anything pulled ----------
    "own-here": [
        "base own cfg",
        "top own cfg",
        "top pull base cfg",
        "top ask cfg",
        "base ask cfg",
    ],
    "own-twice": [
        "base own cfg",
        "base own cfg",
        "base ask cfg",
    ],

    # --- what a pull costs ----------------------------------------------------------------
    "pull-one": [
        "base own cfg",
        "top pull base cfg",
        "top ask cfg",
    ],
    "pull-wide": [
        "base own cfg",
        "base own log",
        "top pull base *",
        "top ask cfg",
        "top ask log",
    ],
    "chain-two": [
        "base own cfg",
        "mid pull base *",
        "top pull mid *",
        "top ask cfg",
    ],
    "cost-max": [
        "far own item",
        "near als box far",
        "mid pull near *",
        "mid pull box item",
        "mid ask box",
        "mid ask item",
    ],
    "cost-src-deep": [
        "far own item",
        "one als box far",
        "two pull one *",
        "three pull two *",
        "mid pull three *",
        "mid pull box item",
        "mid ask box",
        "mid ask item",
    ],

    # --- which units a source name denotes -------------------------------------------------
    "src-both": [
        "far own item",
        "near own item",
        "near als far near",
        "mid pull near *",
        "mid pull far item",
        "mid ask item",
    ],
    "src-ghost": [
        "far own item",
        "near als box ghost",
        "near pull box item",
        "near ask box",
        "near ask item",
    ],
    "src-two-readings": [
        "s own item",
        "t own item",
        "u als s t",
        "u pull s item",
        "u ask item",
    ],
    "cost-both-deep": [
        "far own item",
        "gate pull far *",
        "step pull gate *",
        "one als box step",
        "two pull one *",
        "mid pull two *",
        "mid pull box item",
        "mid ask box",
        "mid ask item",
    ],
    "src-unit-only": [
        "far own item",
        "near own far",
        "near pull far item",
        "near ask item",
    ],

    # --- shut and hide ---------------------------------------------------------------------
    "shut-wide": [
        "core own key",
        "core own tag",
        "core shut tag",
        "side pull core *",
        "side ask key",
        "side ask tag",
    ],
    "shut-narrow": [
        "core own tag",
        "core shut tag",
        "side pull core tag",
        "side ask tag",
    ],
    "hide-both": [
        "core own raw",
        "side pull core *",
        "side pull core raw",
        "core hide raw",
        "side ask raw",
    ],
    "hide-local": [
        "core own raw",
        "core hide raw",
        "core ask raw",
    ],
    "shut-then-on": [
        "core own tag",
        "core shut tag",
        "side pull core tag",
        "far pull side *",
        "far ask tag",
    ],

    # --- only the lowest rank decides -------------------------------------------------------
    "near-wins": [
        "base own cfg",
        "hop pull base *",
        "far pull hop *",
        "top pull base *",
        "top pull far *",
        "top ask cfg",
    ],
    "far-ignored": [
        "one own cfg",
        "two own cfg",
        "hop pull two *",
        "far pull hop *",
        "top pull one *",
        "top pull far *",
        "top ask cfg",
    ],

    # --- one origin binds, two clash ---------------------------------------------------------
    "two-origins": [
        "one own cfg",
        "two own cfg",
        "top pull one *",
        "top pull two *",
        "top ask cfg",
    ],
    "same-origin-twice": [
        "base own cfg",
        "left pull base *",
        "right pull base *",
        "top pull left *",
        "top pull right *",
        "top ask cfg",
    ],
    "dup-line": [
        "base own cfg",
        "top pull base cfg",
        "top pull base cfg",
        "top ask cfg",
    ],
    "unit-versus-own": [
        "far own item",
        "one own box",
        "two als box far",
        "top pull one *",
        "top pull two *",
        "top ask box",
    ],

    # --- a clash carries nothing onward ------------------------------------------------------
    "clash-stops": [
        "one own cfg",
        "two own cfg",
        "mid pull one *",
        "mid pull two *",
        "top pull mid cfg",
        "mid ask cfg",
        "top ask cfg",
    ],
    "clash-not-wide": [
        "one own cfg",
        "two own cfg",
        "mid pull one *",
        "mid pull two *",
        "top pull mid *",
        "top ask cfg",
    ],
    "kind-clash": [
        "far own box",
        "one pull far box",
        "two als box far",
        "mid pull two *",
        "top pull one *",
        "top pull mid *",
        "top ask box",
    ],
    "clash-then-one": [
        "one own cfg",
        "two own cfg",
        "hop pull one *",
        "mid pull one *",
        "mid pull two *",
        "mid pull hop *",
        "mid ask cfg",
    ],
    "clash-around": [
        "one own cfg",
        "two own cfg",
        "mid pull one *",
        "mid pull two *",
        "top pull mid *",
        "top pull one cfg",
        "top ask cfg",
    ],

    # --- settled in rank order, and never re-settled from a later fact -------------------------
    "late-clash": [
        "p pull a x",
        "m pull p x",
        "m pull q x",
        "t pull m x",
        "t ask x",
        "m ask x",
        "q pull b x",
        "a own x",
        "b own x",
    ],
    "late-clash-swap": [
        "a own x",
        "b own x",
        "q pull b x",
        "m ask x",
        "t ask x",
        "t pull m x",
        "m pull q x",
        "m pull p x",
        "p pull a x",
    ],
    "late-near": [
        "t pull m x",
        "t ask x",
        "m pull hop x",
        "m pull a x",
        "hop pull b x",
        "a own x",
        "b own x",
    ],

    # --- cycles -------------------------------------------------------------------------------
    "ring-two": [
        "a pull b *",
        "a own one",
        "b pull a *",
        "b own two",
        "c pull a *",
        "c ask one",
        "c ask two",
    ],
    "ring-race": [
        "x own v",
        "y own v",
        "a pull x *",
        "b pull y *",
        "m pull a *",
        "m pull b *",
        "m pull n *",
        "n pull m *",
        "m ask v",
        "n ask v",
    ],
    "ring-only": [
        "a pull b *",
        "b pull a *",
        "a ask one",
    ],

    # --- what an ask reports -------------------------------------------------------------------
    "ask-unit": [
        "far own item",
        "near als box far",
        "near ask box",
    ],
    "ask-none": [
        "base own cfg",
        "top pull base *",
        "top ask log",
    ],
    "wide-carries-unit": [
        "far own item",
        "near als box far",
        "top pull near *",
        "top ask box",
    ],
}

ORDER = sorted(CASES)


def ops(name):
    return list(CASES[name])
