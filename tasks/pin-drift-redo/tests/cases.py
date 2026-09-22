"""The enumerated programs: one per graded decision, plus the side that must still work.

Each name says which rule its program decides, and each is small enough to read by hand. The
answers live in the sealed `gt.json`, frozen from the model before the grading file was
written; the grader checks the model still reproduces them before it grades anything.
"""

PROGS = {
    # --- the ordinary side: nothing moves, nothing is cut -----------------------------
    "plain-run": """
        cfg 4 | tx 1 | add 1 0 7 | cpy 1 1 0 | rd 1 1 | put 1 2 5 | fin 1""",
    "no-move-no-redo": """
        cfg 4 | tx 1 | add 1 0 3 | tx 2 | put 2 1 9 | fin 2 | add 1 0 4 | fin 1""",
    "cond-all-stand": """
        cfg 5 | tx 1 | mk 1 | put 1 0 6 | chk 1 0 6 | lim 1 0 6 | put 1 1 2 | fin 1""",

    # --- taking a basis ---------------------------------------------------------------
    "take-first-touch": """
        cfg 3 | tx 1 | tx 2 | put 2 0 40 | fin 2 | add 1 0 2 | fin 1""",
    "retake-on-touch": """
        cfg 3 | tx 1 | add 1 0 1 | tx 2 | put 2 0 50 | fin 2 | add 1 0 1 | fin 1""",
    "retake-shows-in-read": """
        cfg 3 | tx 1 | add 1 0 1 | tx 2 | put 2 0 50 | fin 2 | rd 1 0 | fin 1""",
    "put-still-takes": """
        cfg 4 | tx 1 | cpy 1 1 0 | tx 2 | put 2 0 30 | fin 2 | put 1 0 7 | rd 1 1 | fin 1""",
    "retake-at-close": """
        cfg 3 | tx 1 | add 1 0 5 | tx 2 | put 2 0 30 | fin 2 | fin 1""",
    "retake-both-kinds": """
        cfg 4 | tx 1 | add 1 0 5 | put 1 1 5 | tx 2 | put 2 0 10 | put 2 1 10 | fin 2 | fin 1""",
    "two-open-one-key": """
        cfg 3 | tx 1 | tx 2 | add 1 0 1 | add 2 0 2 | fin 1 | fin 2""",

    # --- what the work makes of a basis ----------------------------------------------
    "redo-through-copy": """
        cfg 4 | tx 1 | add 1 0 3 | cpy 1 1 0 | tx 2 | put 2 0 20 | fin 2 | fin 1""",
    "put-not-owed": """
        cfg 3 | tx 1 | put 1 0 9 | tx 2 | put 2 0 30 | fin 2 | fin 1""",
    "copy-holds-own": """
        cfg 4 | tx 1 | add 1 0 6 | cpy 1 1 0 | fin 1""",
    "add-sources-before": """
        cfg 4 | tx 1 | add 1 0 2 | cpy 1 1 0 | add 1 0 5 | fin 1""",
    "raw-ignores-own": """
        cfg 4 | tx 1 | put 1 0 50 | raw 1 1 0 | fin 1""",
    "raw-follows-basis": """
        cfg 4 | tx 1 | raw 1 1 0 | tx 2 | put 2 0 33 | fin 2 | fin 1""",
    "bmp-takes-range": """
        cfg 5 | tx 1 | add 1 2 1 | tx 2 | put 2 2 20 | fin 2 | bmp 1 1 4 3 | fin 1""",
    "bmp-retakes-range": """
        cfg 5 | tx 1 | add 1 2 1 | tx 2 | put 2 2 20 | fin 2 | bmp 1 1 4 3 | rd 1 2 | fin 1""",
    "bmp-moves-copy": """
        cfg 5 | tx 1 | cpy 1 0 2 | tx 2 | put 2 2 20 | fin 2 | bmp 1 1 4 3 | rd 1 0 | fin 1""",
    "bmp-adds-each": """
        cfg 5 | tx 1 | put 1 1 4 | bmp 1 0 3 2 | fin 1""",

    # --- a read fixes ------------------------------------------------------------------
    "read-fixes": """
        cfg 3 | tx 1 | add 1 0 4 | rd 1 0 | tx 2 | put 2 0 70 | fin 2 | fin 1""",
    "read-holds-own": """
        cfg 3 | tx 1 | put 1 0 12 | rd 1 0 | fin 1""",
    "read-then-copy": """
        cfg 4 | tx 1 | rd 1 0 | cpy 1 0 1 | tx 2 | put 2 1 25 | fin 2 | fin 1""",
    "read-no-write": """
        cfg 3 | tx 1 | rd 1 1 | put 1 0 3 | fin 1""",

    # --- marks and cuts ----------------------------------------------------------------
    "undo-drops-writes": """
        cfg 4 | tx 1 | put 1 0 5 | mk 1 | put 1 1 9 | add 1 0 2 | un 1 | fin 1""",
    "undo-restores-owed": """
        cfg 4 | tx 1 | cpy 1 1 0 | mk 1 | put 1 1 99 | un 1 | tx 2 | put 2 0 60 | fin 2 | fin 1""",
    "undo-owes-after-mark": """
        cfg 4 | tx 1 | cpy 1 1 0 | mk 1 | put 1 1 99 | un 1 | tx 2 | put 2 0 60 | fin 2
        | add 1 0 0 | rd 1 1 | fin 1""",
    "undo-no-mark": """
        cfg 3 | tx 1 | put 1 0 8 | un 1 | put 1 1 2 | fin 1""",

    # --- conditions, tested at the close ------------------------------------------------
    "cond-at-close": """
        cfg 4 | tx 1 | mk 1 | add 1 0 5 | chk 1 0 5 | put 1 1 7 | tx 2 | put 2 0 30 | fin 2 | fin 1""",
    "cond-holds-later": """
        cfg 4 | tx 1 | mk 1 | add 1 0 5 | chk 1 0 35 | put 1 1 7 | tx 2 | put 2 0 30 | fin 2 | fin 1""",
    "cond-at-its-place": """
        cfg 4 | tx 1 | mk 1 | put 1 0 5 | chk 1 0 5 | put 1 0 9 | fin 1""",
    "cond-no-mark": """
        cfg 3 | tx 1 | put 1 0 4 | chk 1 0 9 | fin 1""",
    "cut-and-carry-on": """
        cfg 5 | tx 1 | put 1 0 1 | mk 1 | put 1 1 2 | chk 1 1 99 | put 1 2 3 | fin 1""",
    "cut-feeds-next": """
        cfg 5 | tx 1 | put 1 0 10 | mk 1 | add 1 0 5 | chk 1 0 99 | chk 1 0 10 | put 1 1 1 | fin 1""",
    "nest-inner-first": """
        cfg 5 | tx 1 | mk 1 | put 1 0 1 | mk 1 | put 1 1 2 | chk 1 1 99 | put 1 2 3 | fin 1""",
    "nest-outer-next": """
        cfg 5 | tx 1 | mk 1 | put 1 0 1 | mk 1 | put 1 1 2 | chk 1 1 99 | chk 1 0 99 | put 1 2 3 | fin 1""",
    "lim-at-n": """
        cfg 4 | tx 1 | mk 1 | put 1 0 6 | lim 1 0 6 | put 1 1 1 | fin 1""",
    "lim-below-n": """
        cfg 4 | tx 1 | mk 1 | put 1 0 5 | lim 1 0 6 | put 1 1 1 | fin 1""",

    # --- what a close writes -------------------------------------------------------------
    "publish-after-cut": """
        cfg 5 | tx 1 | put 1 0 4 | mk 1 | put 1 0 9 | chk 1 0 99 | fin 1""",
    "publish-drops-key": """
        cfg 5 | tx 1 | put 1 0 4 | mk 1 | put 1 1 9 | chk 1 1 99 | fin 1""",
    "publish-order": """
        cfg 5 | tx 1 | put 1 3 1 | put 1 0 2 | put 1 2 3 | fin 1""",
    "publish-unchanged": """
        cfg 3 | tx 1 | add 1 0 0 | fin 1""",
    "publish-none": """
        cfg 3 | tx 1 | rd 1 0 | fin 1""",
    "drop-writes-nothing": """
        cfg 3 | tx 1 | put 1 0 5 | drp 1 | tx 2 | rd 2 0 | fin 2""",
}

ORDER = sorted(PROGS)


def prog(name):
    return [bit.strip() for bit in PROGS[name].replace("\n", " ").split("|") if bit.strip()]
