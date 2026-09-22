"""The enumerated segment files: one per graded decision, and both sides of every fence.

Each name says which rule its file pins. The frozen answers are in `seal/gt.json`, and the
grader checks the sealed model still reproduces them before it grades anything, so a model
that had drifted cannot quietly redefine what these files mean.

The `hdr-` files pin the two sound header tests and the widened bounds an inexact header
stands for. The `dic-` files pin when a dictionary may decide, what each verdict does and that
a chunk's dictionary is charged once. The `ord-` files pin the choice: smallest expected
survivors, the cap by the chunk's survivors, the exact count of a chunk that has been read,
and the two tie-breaks. The `dec-` files pin what a read settles. The `prj-` files pin the
report pass. The rest fence the ordinary cases a wrong repair breaks: a query where nothing
prunes, a query that keeps everything, and two queries that must not share state.
"""

CASES = {}


def _add(name, text):
    CASES[name] = [ln for ln in text.strip("\n").split("\n")]


# --- headers: the widened bounds an inexact recorded pair stands for -------------------

_add("hdr-widen-high", """
seg 10 4 2
ch 0 4 0 30 40 w p 21 34 48 40
ch 1 4 0 5 8 e p 5 6 7 8
qry
prd ge 0 45
prj 0
end
""")

_add("hdr-widen-low", """
seg 10 4 2
ch 0 4 0 30 40 w p 21 34 48 40
ch 1 4 0 5 8 e p 5 6 7 8
qry
prd le 0 25
prj 0
end
""")

_add("hdr-widen-eq", """
seg 10 4 2
ch 0 4 0 30 30 w p 28 30 33 30
ch 1 4 0 5 8 e p 5 6 7 8
qry
prd eq 0 30
prj 0
end
""")

_add("hdr-widen-ne", """
seg 10 4 2
ch 0 4 0 30 30 w p 28 30 33 30
ch 1 4 0 5 8 e p 5 6 7 8
qry
prd ne 0 30
prj 0
end
""")

# --- headers: the two sound tests, on both sides --------------------------------------

_add("hdr-miss-skip", """
seg 10 8 2
ch 0 4 0 5 8 e p 5 6 7 8
ch 0 4 0 20 30 e p 20 24 27 30
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ge 0 22
prj 1
end
""")

_add("hdr-all-pass", """
seg 10 8 2
ch 0 4 0 20 30 e p 20 24 27 30
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ge 0 10
prj 1
end
""")

_add("hdr-nulls-block-pass", """
seg 10 8 2
ch 0 4 2 20 25 e p 20 - 25 -
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ge 0 10
prj 1
end
""")

_add("hdr-ne-exact-miss", """
seg 10 8 2
ch 0 4 0 7 7 e p 7 7 7 7
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ne 0 7
prj 1
end
""")

_add("hdr-null-chunk-null", """
seg 10 8 2
ch 0 4 4 - - e p - - - -
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd nu 0
prj 1
end
qry
prd nn 0
prj 1
end
""")

_add("hdr-nu-no-nulls", """
seg 10 8 2
ch 0 4 0 20 30 e p 20 24 27 30
ch 0 4 2 40 50 e p 40 - 47 -
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd nu 0
prj 0
end
""")

# --- dictionaries: when one may decide, what each verdict does, and the charge ---------

_add("dic-whole-drop", """
seg 10 8 2
ch 0 4 0 3 9 e d 2 3 9 0 1 0 1
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd eq 0 5
prj 1
end
""")

_add("dic-whole-keep", """
seg 10 8 2
ch 0 4 0 3 9 e d 2 3 9 0 1 0 1
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ne 0 5
prj 1
end
""")

_add("dic-whole-read", """
seg 10 8 2
ch 0 4 0 3 9 e d 2 3 9 0 1 0 1
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ge 0 5
prj 1
end
""")

_add("dic-overflow-read", """
seg 10 8 2
ch 0 4 0 3 9 e d 2 3 9 0 *7 0 1
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd eq 0 7
prj 1
end
""")

_add("dic-charge-once", """
seg 10 8 2
ch 0 4 0 3 9 e d 2 3 9 0 1 0 1
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ne 0 5
prd ge 0 5
prj 1
end
""")

_add("dic-nulls-read", """
seg 10 8 2
ch 0 4 1 3 9 e d 2 3 9 0 - 0 1
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ne 0 5
prj 1
end
""")

_add("dic-not-for-null", """
seg 10 8 2
ch 0 4 1 3 9 e d 2 3 9 0 - 0 1
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd nn 0
prj 1
end
""")

# --- the report pass -------------------------------------------------------------------

_add("prj-dead-chunk", """
seg 10 8 2
ch 0 4 0 5 8 e p 5 6 7 8
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 4 0 1 2 e p 1 2 1 2
ch 1 4 0 3 4 e p 3 4 3 4
qry
prd ge 0 20
prj 1
end
""")

_add("prj-listed-order", """
seg 10 4 3
ch 0 4 0 20 30 e p 20 24 27 30
ch 1 4 0 1 2 e p 1 2 1 2
ch 2 4 0 7 8 e p 7 8 7 8
qry
prd ge 0 10
prj 2 1
end
""")

_add("prj-same-twice", """
seg 10 4 2
ch 0 4 0 20 30 e p 20 24 27 30
ch 1 4 0 1 2 e p 1 2 1 2
qry
prd ge 0 10
prj 1 1
end
""")

_add("prj-nulls-out", """
seg 10 4 2
ch 0 4 0 20 30 e p 20 24 27 30
ch 1 4 2 1 2 e p 1 - 2 -
qry
prd ge 0 10
prj 1
end
""")

_add("prj-reuse-read", """
seg 10 4 2
ch 0 4 1 20 30 e p 20 - 27 30
ch 1 4 0 1 2 e p 1 2 1 2
qry
prd ge 0 22
prj 0
end
""")

# --- ordinary cases a wrong repair breaks ------------------------------------------------

_add("ord-nothing-prunes", """
seg 10 12 2
ch 0 6 0 10 20 e p 10 12 14 16 18 20
ch 0 6 0 10 20 e p 11 13 15 17 19 20
ch 1 4 0 30 40 e p 30 34 37 40
ch 1 4 0 30 40 e p 31 35 38 40
ch 1 4 0 30 40 e p 32 36 39 40
qry
prd ge 0 12
prd le 1 38
prj 0 1
end
""")

_add("ord-keeps-all", """
seg 10 8 2
ch 0 4 0 20 30 e p 20 24 27 30
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ge 0 5
prd le 1 9
prj 0 1
end
""")

_add("qry-starts-over", """
seg 10 8 2
ch 0 4 0 3 9 e d 2 3 9 0 1 0 1
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ge 0 5
prj 1
end
qry
prd ge 0 5
prj 1
end
""")

_add("sel-empty", """
seg 10 8 2
ch 0 4 0 5 8 e p 5 6 7 8
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd ge 0 60
prj 0 1
end
""")



# --- the order: the interpolation, the exact count and what a read settles --------------

_add("ord-spread-rounds-up", """
seg 10 4 2
ch 0 4 0 3 9 e p 3 5 7 9
ch 1 2 0 0 1 e p 0 1
ch 1 2 0 0 1 e p 0 1
qry
prd eq 1 1
prd eq 0 5
prj 0
end
""")

_add("ord-spread-takes-edge", """
seg 10 4 2
ch 0 4 0 3 9 e p 3 5 7 9
ch 1 2 0 0 1 e p 0 1
ch 1 2 0 0 1 e p 0 1
qry
prd eq 1 1
prd ge 0 9
prj 0
end
""")

_add("ord-exact-after-read", """
seg 10 8 2
ch 0 8 0 10 17 e p 10 10 10 10 10 10 10 17
ch 1 4 0 0 3 e p 0 1 2 3
ch 1 4 0 0 3 e p 0 1 2 3
qry
prd ge 0 15
prd eq 0 10
prd le 1 1
prj 1
end
""")

_add("dic-drop-with-nulls", """
seg 10 8 2
ch 0 4 1 3 9 e d 2 3 9 0 - 0 1
ch 0 4 0 40 50 e p 40 44 47 50
ch 1 8 0 1 2 e p 1 2 1 2 1 2 1 2
qry
prd eq 0 5
prj 1
end
""")

_add("dec-hits-whole-chunk", """
seg 10 8 3
ch 0 8 0 5 9 e p 5 5 5 5 9 9 9 9
ch 1 4 0 0 0 e p 0 0 0 0
ch 1 4 0 1 1 e p 1 1 1 1
ch 2 8 0 1 8 e p 1 2 3 4 5 6 7 8
qry
prd ge 0 6
prd le 1 0
prd eq 0 5
prd le 2 2
prj 2
end
""")


ORDER = sorted(CASES)


def prog(name):
    return CASES[name]
