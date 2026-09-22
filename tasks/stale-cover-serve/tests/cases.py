"""The enumerated programs, one per rule and per wrong reading.

Each name says which decision the program pins, so a failure names a rule instead of reading
as bad luck on a random program. The generated population is what proves generality; this set
is what makes a failure legible, and `tools/readingcheck.py` measures that every reading
written down in authoring/ is failed by the case named for it.

These are ordinary readable programs, so they are also the set a submission could in principle
be fitted to. That is what the generated population, seeded after the agent's container is
gone, exists to prevent.
"""

CASES = {

    # A read with nothing cached fetches the whole range and answers at the present version.
    "cold-miss": """
h 20 0 8
w 1 5
w 3 7
c
r 0 4 0
""",

    # A range wholly inside current stretches is answered without going to the store.
    "fresh-cover": """
h 20 0 8
w 1 5
c
r 0 4 0
r 1 3 0
r 0 4 2
""",

    # One version back is still a whole cover, so an allowance of one avoids the fetch.
    "serve-back-one": """
h 20 0 8
w 1 5
w 3 7
c
r 0 4 0
w 2 9
c
r 0 4 1
""",

    # The same read with no allowance has to go to the store.
    "zero-forces-fetch": """
h 20 0 8
w 1 5
w 3 7
c
r 0 4 0
w 2 9
c
r 0 4 0
""",

    # Two halves that were never correct at the same version are not an answer.
    "no-torn-cover": """
h 40 0 8
w 0 1
w 3 2
w 6 3
w 9 4
c
r 0 4 0
w 2 8
c
w 7 9
c
r 5 9 0
r 0 9 30
""",

    # Covers exist at two versions; the newer one is served.
    "newest-wins": """
h 40 0 8
w 1 5
c
r 0 3 0
w 1 6
c
r 0 3 0
w 2 7
c
r 0 3 5
""",

    # No allowed version has a whole cover, so the holes are the ones open now.
    "gap-at-now": """
h 40 0 8
w 0 1
w 5 2
c
r 0 3 0
w 1 9
w 5 3
c
r 4 7 0
r 0 7 6
""",

    # A fetch is correct from the store's last write, so it answers reads aimed before it.
    "learn-the-past": """
h 200 0 8
w 0 1
w 4 2
c
r 0 2 0
w 1 7
c
w 8 3
c
r 3 5 0
r 0 5 3
""",

    # A fetch that comes back empty is correct from the delete, not from the beginning.
    "empty-not-old": """
h 200 0 8
w 0 4
w 5 1
c
r 0 3 0
w 2 7
c
x 5
c
w 8 1
c
r 4 6 0
r 0 6 4
""",

    # A commit ends validity at the version before it, not at its own.
    "close-before": """
h 200 0 8
w 0 1
c
r 0 2 0
w 1 5
c
r 0 2 0
""",

    # Storing the value a key already holds is still a write.
    "same-value-write": """
h 200 0 8
w 0 1
w 2 3
c
r 0 3 0
w 2 3
c
r 0 3 0
""",

    # Deleting a key that is not there is still a write.
    "absent-delete": """
h 200 0 8
w 0 1
c
r 0 3 0
x 2
c
r 0 3 0
""",

    # A stretch the present has left behind keeps answering reads aimed at its own versions.
    "keep-closed": """
h 200 0 8
w 0 1
c
r 0 3 0
w 1 5
c
r 0 3 1
r 0 3 1
""",

    # Past the horizon the older version is gone and the read has to fetch.
    "horizon-drops": """
h 2 0 8
w 0 1
c
r 0 3 0
w 1 5
c
w 1 6
c
w 1 7
c
r 0 3 9
""",

    # A stretch whose last correct version sits exactly on the horizon is kept.
    "horizon-edge": """
h 2 0 8
w 0 1
c
r 0 3 0
w 1 5
c
w 1 6
c
r 0 3 9
""",

    # The horizon never discards a stretch that is still current, however old it is.
    "horizon-open": """
h 2 0 8
w 0 1
w 9 1
c
r 0 3 0
w 9 2
c
w 9 3
c
w 9 4
c
r 0 3 0
""",

    # A horizon of zero drops a stretch on the commit that closed it.
    "horizon-zero": """
h 0 0 8
w 0 1
c
r 0 3 0
w 1 5
c
r 0 3 9
""",

    # Two stretches of one cover share keys; the answer lists each key once.
    "dupe-keys": """
h 200 0 8
w 0 1
w 3 2
c
r 0 4 0
w 0 9
c
r 2 3 0
w 8 1
c
r 0 4 3
""",

    # The cover was built right half first; the answer is still in key order.
    "row-order": """
h 200 0 8
w 1 5
w 6 7
c
r 5 8 0
r 0 3 0
r 0 8 0
""",

    # The only cover sits exactly at the oldest version the allowance permits.
    "floor-edge": """
h 200 0 8
w 0 1
c
r 0 3 0
w 1 5
c
w 1 6
c
w 1 7
c
r 0 3 3
r 0 3 2
""",

    # Two holes, one fetch each, in increasing key order.
    "two-holes": """
h 200 0 8
w 1 1
w 5 2
w 9 3
c
r 4 6 0
r 0 9 0
""",

    # A hole of one key is one fetch, and a range with no rows prints nothing.
    "single-hole": """
h 200 0 8
w 2 1
c
r 0 1 0
r 3 4 0
r 0 4 0
""",

    # A commit that stages nothing still makes a version.
    "empty-commit": """
h 200 0 8
w 0 1
c
r 0 3 0
c
r 0 3 0
""",

    # Two writes of one key in a batch leave the later value and one write.
    "dup-staged": """
h 200 0 8
w 0 1
c
r 0 3 0
w 1 5
w 1 6
c
r 0 3 0
""",

    # A read before any commit is answered at version zero.
    "read-at-zero": """
h 200 0 8
r 0 3 0
w 0 1
c
r 0 3 0
""",

    # An allowance larger than the whole history reaches back to version zero.
    "wide-allowance": """
h 200 0 8
w 0 1
c
r 0 3 0
w 1 5
c
r 0 3 99
""",

    # A stretch sitting inside the requested range leaves a hole on each side.
    "nested-cover": """
h 200 0 8
w 1 1
w 5 2
c
r 2 4 0
r 0 6 0
r 1 5 0
""",

    # One commit ends two stretches, and the pair still covers the older version together.
    "cascade-close": """
h 200 0 8
w 0 1
w 5 2
c
r 0 2 0
r 3 6 0
w 1 7
w 5 8
c
r 0 6 1
r 0 6 0
""",

    # A key deleted since is absent now and present at the version the allowance reaches.
    "delete-visible": """
h 200 0 8
w 2 5
c
r 0 3 0
x 2
c
r 0 3 1
r 0 3 0
""",

    # No allowance at all still takes a current cover rather than the store.
    "zero-hit": """
h 200 0 8
w 0 1
c
r 0 3 0
r 0 3 0
r 1 2 0
""",

    # Part of the range was never cached, so no version has a whole cover.
    "no-cover-any": """
h 200 0 8
w 0 1
w 7 2
c
r 0 2 0
r 0 7 99
""",

    # Two holes with one cached key between them are one round trip when the slack allows it.
    "combine-two": """
h 200 1 8
w 0 1
w 2 2
w 4 3
c
r 2 2 0
r 0 4 0
""",

    # One key further apart and the same slack leaves them as two.
    "combine-edge": """
h 200 1 8
w 0 1
w 2 2
w 3 6
w 5 3
c
r 2 3 0
r 0 5 0
""",

    # Past the cap the whole requested range is taken, not the span of the runs.
    "cap-whole": """
h 200 0 1
w 0 1
w 2 2
w 4 3
c
r 0 0 0
r 2 2 0
r 4 4 0
r 0 6 0
""",

    # Exactly as many runs as the cap allows is not past it.
    "cap-edge": """
h 200 0 2
w 0 1
w 2 2
w 4 3
c
r 2 2 0
r 0 4 0
""",

    # The cap counts the runs left after combining, not the holes before it.
    "combine-then-cap": """
h 200 1 2
w 0 1
w 3 2
w 5 3
w 7 4
w 9 5
c
r 2 2 0
r 4 6 0
r 8 8 0
r 0 9 0
""",

    # A combined run is one piece of knowledge: what comes back is kept as the run it was
    # fetched in, not carved back up into the holes it was made of.
    "install-run-whole": """
h 200 2 3
r 9 15 0
r 8 12 0
w 12 13
c
r 5 9 0
w 7 31
c
r 5 9 0
""",
}

ORDER = [
    "cold-miss",
    "fresh-cover",
    "serve-back-one",
    "zero-forces-fetch",
    "no-torn-cover",
    "newest-wins",
    "gap-at-now",
    "learn-the-past",
    "empty-not-old",
    "close-before",
    "same-value-write",
    "absent-delete",
    "keep-closed",
    "horizon-drops",
    "horizon-edge",
    "horizon-open",
    "horizon-zero",
    "dupe-keys",
    "row-order",
    "floor-edge",
    "two-holes",
    "single-hole",
    "empty-commit",
    "dup-staged",
    "read-at-zero",
    "wide-allowance",
    "nested-cover",
    "cascade-close",
    "delete-visible",
    "zero-hit",
    "no-cover-any",
    "combine-two",
    "combine-edge",
    "cap-whole",
    "cap-edge",
    "combine-then-cap",
    "install-run-whole",
]


def prog(name):
    return CASES[name].strip("\n").split("\n")
