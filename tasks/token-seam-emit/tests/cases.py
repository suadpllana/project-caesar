"""The enumerated requests.

Every entry is aimed at one decision, and every entry is separated by at least one wrong
reading in `authoring/token-seam-emit/readings.py` - so a failure here names the rule that
was misread rather than reporting that something, somewhere, differed.

The generated set is what stops a submission fitting these; these are what make a failure
legible. Piece ids come from the piece table, and the comment on each line says what the
request is built to decide.

A spec is (floor, cap, stops, ids).
"""

CASES = [
    # No stop strings at all: the release point is the character boundary and nothing else.
    ("plain-eos", (0, 20, [], [23, 24, 25, 26, 31, 1])),
    ("plain-length", (0, 5, [], [23, 24, 25, 26, 31])),
    ("plain-floor-high", (9, 20, [], [23, 24, 25, 26, 31, 1])),

    # A live partial is held, then released once the tail can no longer grow into the stop.
    ("partial-hold", (0, 20, [b"abc"], [23, 24, 10, 3, 4, 6, 7, 1])),
    ("partial-release", (0, 20, [b"abc"], [23, 3, 4, 9, 9, 9, 1])),
    ("partial-long", (0, 20, [b"the of"], [27, 28, 27, 28, 9, 1])),

    # The floor regime. An occurrence that completes below the floor does not terminate the
    # request, but it pins the release point where it starts and the request ends there at
    # the first step at or after the floor.
    ("stop-no-floor", (0, 20, [b"abc"], [23, 24, 10, 3, 4, 5, 6, 7, 1])),
    ("stop-below-floor", (8, 20, [b"abc"], [23, 24, 10, 3, 4, 5, 6, 7, 8, 9, 1])),
    ("stop-far-below-floor", (12, 24, [b"abc"], [19, 6, 7, 8, 9, 6, 7, 8, 9, 6, 7, 8, 9, 1])),
    ("stop-at-floor-exact", (6, 20, [b"abc"], [23, 24, 10, 3, 4, 5, 6, 1])),
    ("stop-one-below-floor", (7, 20, [b"abc"], [23, 24, 10, 3, 4, 5, 6, 1])),
    ("no-occurrence-at-floor", (6, 20, [b"abc"], [23, 24, 10, 3, 4, 9, 6, 7, 1])),
    ("floor-equals-cap", (6, 6, [b"abc"], [23, 3, 4, 5, 6, 7])),
    ("occurrence-at-zero", (4, 20, [b"abc"], [19, 6, 7, 8, 9, 1])),

    # End of stream. The floor suppresses the terminator, not the piece.
    ("eos-below-floor", (9, 20, [], [23, 24, 1, 25, 26, 31, 7, 8, 9, 1])),
    ("eos-at-floor", (3, 20, [], [23, 24, 1, 25, 26])),
    ("eos-below-floor-with-stop", (9, 20, [b"abc"], [23, 1, 3, 4, 5, 6, 7, 8, 9, 1])),
    ("cap-holding-partial", (0, 4, [b"abcd"], [23, 3, 4, 5])),
    ("cap-with-occurrence", (0, 5, [b"abc"], [23, 24, 3, 4, 5])),

    # Character seams, including one that straddles a special piece.
    ("seam-two-byte", (0, 20, [], [23, 43, 44, 24, 1])),
    ("seam-three-byte", (0, 20, [], [23, 54, 47, 24, 1])),
    ("seam-four-byte", (0, 20, [], [23, 48, 49, 50, 51, 24, 1])),
    ("seam-straddle-piece", (0, 20, [], [23, 55, 56, 24, 1])),
    ("seam-across-special", (0, 20, [], [23, 43, 0, 44, 24, 1])),
    ("seam-trailing-incomplete", (0, 20, [], [23, 24, 48, 49, 1])),
    ("seam-whole-chars", (0, 20, [], [40, 41, 42, 1])),

    # A stop string the client text contains only because a special piece contributes
    # nothing to it.
    ("occurrence-across-special", (0, 20, [b"abc"], [23, 3, 4, 0, 5, 6, 1])),
    ("occurrence-across-special-floor", (8, 20, [b"abc"], [23, 3, 4, 2, 5, 6, 7, 8, 9, 1])),

    # The one leading space, dropped once, which moves every match position after it.
    ("lead-space", (0, 20, [b"abc"], [17, 4, 5, 6, 1])),
    ("lead-space-only", (0, 20, [], [10, 23, 24, 1])),

    # Several stop strings, and stop strings that overlap.
    ("two-stops-earliest", (0, 20, [b"abc", b"llo"], [23, 24, 3, 4, 5, 1])),
    ("nested-stops", (0, 20, [b"ab", b"abc"], [23, 3, 4, 5, 6, 1])),
    # A longer stop that completes later but starts earlier than one already standing.
    # An implementation that remembers the first occurrence it saw and stops looking
    # releases a byte here that the request never sends.
    ("later-stop-starts-earlier", (6, 12, [b"abcd", b"bc"], [3, 4, 5, 6, 9, 9, 9, 1])),
    ("later-stop-starts-earlier-long", (8, 14, [b"abcd", b"bc"], [3, 4, 5, 6, 9, 9, 9, 9, 1])),
    ("nested-stop-same-end", (5, 12, [b"xyz", b"yz"], [23, 7, 8, 9, 6, 7, 1])),

    ("single-byte-stop", (0, 20, [b"z"], [23, 24, 9, 6, 1])),
    ("newline-stop", (0, 20, [b"\n"], [23, 24, 21, 6, 1])),
    ("multibyte-stop", (0, 20, [b"\xc3\xa9"], [23, 43, 44, 24, 1])),
    ("multibyte-stop-floor", (7, 20, [b"\xc3\xa9"], [23, 43, 44, 24, 6, 7, 8, 9, 1])),
]
