"""The enumerated programs: one per graded decision, and both sides of every fence.

Each is short enough to derive by hand, and each is named for the rule it pins, so a failure
says which rule broke rather than "some generated program was wrong". Their correct traces are
frozen in seal/gt.json, which was written before the grading file and is checked against the
sealed model on every run.

The reading each one exists to separate is recorded beside it; the measurement that says it
actually does is tools/readingcheck.py.
"""

CASES = {
    # --- the line is written when an evaluation finishes, and reads go left to right -----
    "run-order": [
        "def p raw", "def q raw", "def m cap p 9", "def n cap q 9", "def w sum m n",
        "set p 1", "set q 2", "ask w",
    ],
    # --- a source moving without moving the value above it -------------------------------
    "cut-stops": [
        "def x raw", "def y cap x 5", "def z sum y y",
        "set x 3", "ask z", "set x 9", "ask z", "set x 20", "ask z",
    ],
    # --- the check stops at the first read that differs -----------------------------------
    "bail-stops": [
        "def g raw", "def p raw", "def q raw",
        "def m cap p 9", "def n cap q 9", "def w pick g m n",
        "set g 1", "set p 2", "set q 3", "ask w",
        "set g 0", "set p 7", "ask w",
    ],
    # --- an evaluation replaces its read list, so an abandoned arm stops mattering ---------
    "flip-drop": [
        "def g raw", "def p raw", "def q raw",
        "def m cap p 9", "def n cap q 9", "def w pick g m n",
        "set g 1", "set p 2", "set q 3", "ask w",
        "set g 0", "ask w",
        "set p 5", "ask w",
    ],
    # --- a gate with a zero guard never reads its arm --------------------------------------
    "gate-zero": [
        "def g raw", "def u raw", "def h cap u 9", "def k gate g h",
        "set u 4", "ask k", "set u 6", "ask k", "set g 1", "ask k",
    ],
    # --- a pick reads the guard and one arm ------------------------------------------------
    "pick-one": [
        "def g raw", "def p raw", "def q raw",
        "def m cap p 9", "def n cap q 9", "def w pick g m n",
        "set g 0", "set p 4", "set q 5", "ask w", "set p 8", "ask w",
    ],
    # --- a field reached twice in one question is evaluated once -----------------------------
    "twice-once": [
        "def x raw", "def c cap x 30", "def d sum c c", "def e sum d d",
        "set x 5", "ask e",
    ],
    # --- a publication on its own evaluates nothing -------------------------------------------
    "no-ask-no-run": [
        "def x raw", "def y raw", "def c cap x 30", "def e cap y 30",
        "set x 5", "ask c", "set y 9", "set x 6", "ask e",
    ],
    # --- the preview leaves the kept results where they were -----------------------------------
    "pre-keeps": [
        "def x raw", "def c cap x 30", "def d sum c c",
        "set x 5", "ask d", "try x 8", "ask d", "end", "ask d",
    ],
    # --- a field the preview cannot reach is not evaluated inside it ----------------------------
    "pre-share": [
        "def x raw", "def y raw", "def a cap x 9", "def b cap y 9",
        "set x 1", "set y 2", "ask a", "ask b", "try x 7", "ask b", "end",
    ],
    # --- reaching the previewed source is not the question; the value is ------------------------
    "pre-cut": [
        "def x raw", "def c cap x 3", "def d sum c c",
        "set x 5", "ask d", "try x 9", "ask d", "end",
    ],
    # --- inside the block, what the block evaluated stands over what the base kept ---------------
    "layer-first": [
        "def x raw", "def c cap x 30", "def d sum c c", "def e sum c c",
        "set x 5", "ask d", "try x 8", "ask d", "ask e", "end",
    ],
    # --- publishing the previewed value installs the block's results ------------------------------
    "adopt-install": [
        "def x raw", "def c cap x 30", "def d sum c c",
        "set x 5", "ask d", "try x 8", "ask d", "end", "set x 8", "ask d",
    ],
    # --- installed results are checked, not trusted, and an unrelated publication leaves the
    #     layer standing ---------------------------------------------------------------------------
    "adopt-check": [
        "def x raw", "def y raw", "def c cap x 30", "def e sum c y",
        "set x 5", "set y 1", "ask e",
        "try x 8", "ask e", "end",
        "set y 4", "set x 8", "ask e",
    ],
    # --- a different value throws the layer away ---------------------------------------------------
    "adopt-other": [
        "def x raw", "def y raw", "def c cap x 30", "def e sum y y",
        "set x 5", "set y 1", "ask c",
        "try x 8", "ask e", "end",
        "set x 9", "ask e",
    ],
    # --- opening another block throws the standing one away ------------------------------------------
    "adopt-second": [
        "def x raw", "def y raw", "def c cap x 30", "def e sum y y",
        "set x 5", "set y 1", "ask c",
        "try x 8", "ask e", "end",
        "try x 8", "ask c", "end",
        "set x 8", "ask e", "ask c",
    ],
    # --- publishing the value a source already carries is nothing at all -------------------------------
    "same-holds": [
        "def x raw", "def y raw", "def c cap x 30", "def e sum y y",
        "set x 5", "set y 1", "ask c",
        "try x 8", "ask e", "end",
        "set x 5", "set x 8", "ask e",
    ],
    # --- a pin stands whatever moves under it ------------------------------------------------------------
    "pin-stands": [
        "def x raw", "def c cap x 30", "def d sum c c",
        "set x 5", "ask d", "pin d", "set x 7", "ask d", "free d", "ask d",
    ],
    # --- pinning demands the field first -----------------------------------------------------------------
    "pin-takes": [
        "def x raw", "def c cap x 30",
        "set x 5", "pin c", "ask c",
    ],
    # --- a pin inside a block stands there too, and blocks the preview from spreading ----------------------
    "pin-blocks": [
        "def x raw", "def c cap x 30", "def d sum c c",
        "set x 5", "ask d", "pin c", "try x 9", "ask d", "end", "free c", "ask d",
    ],
    # --- several questions in one block, and the block's own settling -------------------------------------
    "block-many": [
        "def x raw", "def y raw", "def c cap x 30", "def d sum c y", "def e sum d c",
        "set x 5", "set y 2", "ask e",
        "try x 11", "ask c", "ask d", "ask e", "end",
        "ask e",
    ],
    # --- the import shorthand --------------------------------------------------------------------------
    "bulk-small": [
        "bulk B 3 97", "ask Bc0", "ask Bc2", "set Ba0 700", "ask Bc0", "ask Bc2",
    ],
}

ORDER = sorted(CASES)


def ops(name):
    return list(CASES[name])
