"""Programs written by hand, one for each graded decision and for both sides of each fence.

Every one is small enough to work through on paper, and each is named for the rule it pins,
so a failure names the rule rather than a line number. The order of ORDER is the order the
frozen answers in seal/gt.json were built in.
"""

PROGS = {
    # --- the walk: how a chunk is taken and where the cursor lands ---------------------
    "chunk-count": [
        "cfg 2", "set 1 1 1 5", "set 9 2 2 6", "set 40 3 3 7",
        "copy", "cut",
    ],
    "chunk-lands": [
        "cfg 3", "set 2 1 1 5", "set 30 2 2 6", "set 31 3 3 7", "set 99 4 4 8",
        "copy", "play 9", "cut",
    ],
    "chunk-empty": [
        "cfg 2", "set 5 1 1 5", "copy", "copy", "set 8 2 2 6", "copy", "cut",
    ],
    "chunk-after-delete": [
        "cfg 2", "set 1 1 1 5", "set 2 2 2 6", "set 3 3 3 7", "set 4 4 4 8",
        "del 2", "del 3", "copy", "cut",
    ],
    "walk-order": [
        "cfg 4", "set 7 1 1 5", "set 3 1 1 6", "set 9 1 1 7",
        "copy", "cut",
    ],

    # --- the marks: which entries a chunk has already reflected ------------------------
    "mark-not-latest": [
        "cfg 1", "set 1 1 1 5", "set 2 2 2 6", "copy", "set 1 3 3 9", "copy",
        "play 9", "cut",
    ],
    "miss-twice": [
        "cfg 1", "set 5 2 3 5", "copy", "del 5", "del 5", "play 9", "cut",
    ],
    "play-then-copy": [
        "cfg 1", "set 1 1 1 5", "set 3 2 2 6", "copy", "set 3 7 7 9", "play 1",
        "copy", "play 9", "cut",
    ],
    "late-aside-order": [
        "cfg 2", "set 4 1 1 5", "set 9 1 1 6", "copy", "set 2 1 1 7", "set 4 8 8 8",
        "play 9", "cut",
    ],
    "mark-per-chunk": [
        "cfg 1", "set 1 1 1 5", "set 2 2 2 6", "copy", "set 2 4 4 9", "copy",
        "play 9", "cut",
    ],
    "mark-boundary": [
        "cfg 1", "set 1 1 1 5", "copy", "play 9", "cut",
    ],
    "mark-after-chunk": [
        "cfg 1", "set 1 1 1 5", "copy", "set 1 3 3 9", "play 9", "cut",
    ],
    "seen-then-move": [
        "cfg 2", "set 1 1 1 5", "set 2 2 2 6", "set 1 1 1 8", "copy",
        "set 1 5 5 4", "play 9", "cut",
    ],

    # --- the replay: ahead, and what happens to an entry that is dropped ---------------
    "ahead-dropped": [
        "cfg 1", "set 1 1 1 5", "set 2 2 2 6", "set 2 7 7 9", "copy", "play 9",
        "copy", "play 9", "cut",
    ],
    "all-ahead": [
        "cfg 4", "set 1 1 1 5", "set 2 2 2 6", "set 3 3 3 7", "play 9", "cut",
    ],
    "zero-play": [
        "cfg 2", "set 1 1 1 5", "play 0", "copy", "cut",
    ],
    "play-partial": [
        "cfg 2", "set 1 1 1 5", "set 2 2 2 6", "copy", "set 1 4 4 9", "set 2 5 5 9",
        "play 3", "play 1", "cut",
    ],
    "late-key": [
        "cfg 2", "set 2 1 1 5", "set 4 2 2 6", "copy", "set 3 3 3 7", "play 9", "cut",
    ],

    # --- moving under the new key -----------------------------------------------------
    "move-leaves-held": [
        "cfg 1", "set 1 1 1 5", "copy", "set 1 2 2 6", "set 1 3 3 7", "play 1",
        "play 9", "cut",
    ],
    "same-fields": [
        "cfg 1", "set 1 1 1 5", "copy", "set 1 1 1 9", "play 9", "cut",
    ],
    "same-aside": [
        "cfg 2", "set 1 1 1 5", "set 2 1 1 6", "copy", "set 2 1 1 9", "play 9", "cut",
    ],
    "move-into-waiting": [
        "cfg 3", "set 1 1 1 5", "set 2 1 1 6", "set 3 2 2 7", "copy",
        "set 1 2 2 8", "play 9", "cut",
    ],

    # --- rows set aside, and who takes a key when it is freed -------------------------
    "aside-order": [
        "cfg 3", "set 1 1 1 5", "set 2 1 1 6", "set 3 1 1 7", "copy", "cut",
    ],
    "free-smallest": [
        "cfg 4", "set 1 1 1 5", "set 8 1 1 6", "set 4 1 1 7", "copy",
        "set 1 9 9 8", "play 9", "cut",
    ],
    "two-waiters": [
        "cfg 3", "set 1 1 1 5", "set 2 1 1 6", "set 3 1 1 7", "copy",
        "del 1", "play 9", "del 2", "play 9", "cut",
    ],
    "drop-no-release": [
        "cfg 3", "set 1 1 1 5", "set 2 1 1 6", "set 3 1 1 7", "copy",
        "set 2 6 6 9", "play 9", "cut",
    ],
    "off-releases": [
        "cfg 2", "set 1 1 1 5", "set 2 1 1 6", "copy", "set 1 7 7 9", "play 9", "cut",
    ],

    # --- deletes ----------------------------------------------------------------------
    "miss-unknown": [
        "cfg 1", "set 1 1 1 5", "set 9 2 2 6", "copy", "del 9", "play 9", "cut",
    ],
    "del-frees": [
        "cfg 2", "set 1 1 1 5", "set 2 1 1 6", "copy", "del 1", "play 9", "cut",
    ],
    "miss-after-move": [
        "cfg 1", "set 1 1 1 5", "copy", "set 1 4 4 6", "play 9", "del 1", "play 9", "cut",
    ],
    "key-reuse": [
        "cfg 2", "set 1 1 1 5", "set 3 2 2 6", "copy", "del 1", "play 9",
        "set 1 8 8 7", "play 9", "cut",
    ],

    # --- the closing line, and the two sides of the fence ------------------------------
    "end-counts": [
        "cfg 4", "set 1 1 1 5", "set 2 1 1 6", "set 3 2 2 7", "set 4 3 3 8",
        "copy", "cut",
    ],
    "ordinary": [
        "cfg 2", "set 1 1 1 5", "set 2 2 2 6", "set 3 3 3 7", "set 4 4 4 8",
        "copy", "play 9", "copy", "play 9", "cut",
    ],
    "cut-loop": [
        "cfg 1", "set 1 1 1 5", "set 2 2 2 6", "set 3 3 3 7", "set 2 9 9 9", "cut",
    ],
}

ORDER = sorted(PROGS)


def prog(name):
    return list(PROGS[name])
