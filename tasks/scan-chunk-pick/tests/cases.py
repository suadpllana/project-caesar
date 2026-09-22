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


# --- rows carrying an update: tested on their own value, and never a reason to read -----

_add("upd-drop-spares", """
seg 10 4 2
ch 0 4 0 5 8 e p 5 6 7 8
ch 1 4 0 1 4 e p 1 2 3 4
up 0 1 30
qry
prd ge 0 20
prj 1 0
end
""")

_add("upd-keep-tests", """
seg 10 4 2
ch 0 4 0 5 8 e p 5 6 7 8
ch 1 4 0 1 4 e p 1 2 3 4
up 0 2 1
qry
prd ge 0 3
prj 1
end
""")

_add("upd-all-moved-no-read", """
seg 10 6 2
ch 0 3 0 0 9 e p 0 5 9
ch 0 3 0 0 9 e p 1 6 8
ch 1 6 0 1 6 e p 1 2 3 4 5 6
up 0 0 7
up 0 1 2
up 0 2 9
qry
prd ge 0 5
prj 1
end
""")

_add("upd-all-moved-no-rd", """
seg 10 6 2
ch 0 3 0 0 9 e d 3 0 5 9 0 1 2
ch 0 3 0 0 9 e p 1 6 8
ch 1 6 0 1 6 e p 1 2 3 4 5 6
up 0 0 7
up 0 1 2
up 0 2 9
qry
prd ge 0 5
prj 1
end
""")

_add("upd-last-held-dies", """
seg 10 6 2
ch 0 6 0 1 6 e p 1 2 3 4 5 6
ch 1 3 0 0 9 e p 0 5 9
ch 1 3 0 0 9 e p 1 6 8
up 1 0 7
up 1 1 2
qry
prd le 0 2
prd ge 1 5
prj 0
end
""")

_add("upd-count-as-written", """
seg 25 134 2
ch 0 23 21 1 2 e p - - - - - - - - - - - - - 2 - - - - - - - 1 -
ch 0 24 19 1 5 e d 3 1 2 5 2 - - - - 2 - - 0 - 1 - 0 - - - - - - - - - - -
ch 0 29 28 1 1 e d 1 1 - - - - - - - - - 0 - - - - - - - - - - - - - - - - - - -
ch 0 23 23 - - e p - - - - - - - - - - - - - - - - - - - - - - -
ch 0 35 32 2 3 e d 2 2 3 0 - - - - - - - - - - - - - - - - - - - - 0 - - - - - - 1 - - - - - -
ch 1 21 19 7 8 e p 7 - - - - - 8 - - - - - - - - - - - - - -
ch 1 33 31 2 11 e p - - - - - - - - - - - - - - 11 - - - - - - - - - - - - - - - - 2 -
ch 1 16 14 6 11 e d 2 6 11 - - - - 1 - 0 - - - - - - - - -
ch 1 27 24 0 0 w d 2 0 4 - - - - - - - - - - - - 1 - - - - - - - - - - 1 0 - -
ch 1 37 35 6 10 e d 2 6 10 - - - - - - 1 - - - - - - - 0 - - - - - - - - - - - - - - - - - - - - - -
up 1 38 8
up 1 41 0
qry
prd nn 1
prd nu 0
prd ge 1 2
prj 1
end
""")

# --- deleted rows: never alive, never counted --------------------------------------------

_add("del-never-alive", """
seg 10 6 2
ch 0 3 0 1 3 e p 1 2 3
ch 0 3 0 4 6 e p 4 5 6
ch 1 6 0 1 6 e p 1 2 3 4 5 6
del 0
del 1
del 2
qry
prd ge 0 2
prj 1
end
""")

_add("del-caps-score", """
seg 10 6 2
ch 0 3 0 0 9 e p 0 5 9
ch 0 3 0 1 20 e p 1 4 20
ch 1 6 0 1 6 e p 1 2 3 4 5 6
del 0
del 1
qry
prd le 0 7
prj 1
end
""")

# --- the report pass needs a chunk only for a value nothing cheaper supplies -------------

_add("prj-moved-no-read", """
seg 10 4 2
ch 0 4 0 1 4 e p 1 2 3 4
ch 1 2 0 10 20 e p 10 20
ch 1 2 0 30 40 e p 30 40
up 1 0 7
up 1 1 -
qry
prd ge 0 1
prj 1
end
""")

_add("prj-void-no-read", """
seg 10 4 2
ch 0 4 0 1 4 e p 1 2 3 4
ch 1 2 2 - - e p - -
ch 1 2 0 30 40 e p 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-pinned-no-read", """
seg 10 4 2
ch 0 4 0 1 4 e p 1 2 3 4
ch 1 2 0 12 12 e p 12 12
ch 1 2 0 30 40 e p 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-widened-not-pinned", """
seg 10 4 2
ch 0 4 0 1 4 e p 1 2 3 4
ch 1 2 0 20 20 w p 20 20
ch 1 2 0 30 40 e p 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-one-entry-rd", """
seg 10 4 2
ch 0 4 0 1 4 e p 1 2 3 4
ch 1 2 0 20 20 w d 1 20 0 0
ch 1 2 0 30 40 e p 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-one-entry-nulls", """
seg 10 4 2
ch 0 4 0 1 4 e p 1 2 3 4
ch 1 2 1 20 20 w d 1 20 0 -
ch 1 2 0 30 40 e p 30 40
qry
prd le 0 3
prj 1
end
""")

# --- the order moves both ways: deaths lower a score, a read can raise one ---------------

_add("ord-read-raises", """
seg 10 87 2
ch 0 15 0 0 0 w p 5 1 5 3 0 1 0 3 2 4 2 1 3 5 2
ch 0 20 1 0 5 e d 6 0 1 2 3 4 5 2 0 4 1 0 5 1 3 3 3 - 4 2 1 2 1 5 4 0 5
ch 0 15 1 0 0 w d 6 0 1 2 3 4 5 0 4 2 4 5 2 0 - 0 2 1 0 3 0 3
ch 0 10 1 0 5 e d 4 1 2 3 5 0 *0 1 *0 1 - 2 *4 1 3
ch 0 12 0 0 0 w d 6 0 1 2 3 4 5 0 2 3 5 2 1 3 4 2 1 2 3
ch 0 15 2 0 5 e p 4 - 1 3 4 5 5 4 3 2 0 5 - 2 5
ch 1 11 1 0 5 e d 6 0 1 2 3 4 5 1 1 1 5 4 - 5 2 0 3 1
ch 1 12 0 0 5 e d 6 0 1 2 3 4 5 0 0 0 1 0 2 4 4 3 2 4 5
ch 1 15 2 0 0 w d 6 0 1 2 3 4 5 3 5 1 1 2 5 - 3 4 - 5 4 0 1 1
ch 1 21 4 0 0 w d 4 0 2 3 4 *5 *1 2 1 0 *1 - 0 - - 0 3 1 0 *5 *1 0 1 1 2 -
ch 1 18 0 0 0 w d 6 0 1 2 3 4 5 2 2 0 4 2 2 5 0 5 3 1 5 2 5 4 1 2 0
ch 1 10 1 0 5 e d 5 0 2 3 4 5 4 1 4 0 4 3 1 2 4 -
qry
prd ge 1 0
prd ge 0 0
prd ge 0 1
prj 0
end
""")

_add("ord-read-rescored", """
seg 10 66 2
ch 0 14 0 43 128 e p 123 107 121 112 128 53 58 60 55 65 49 59 43 49
ch 0 15 0 41 112 e p 100 87 66 97 112 71 41 49 98 59 42 102 73 108 72
ch 0 11 0 51 128 e p 97 78 52 93 64 92 106 77 51 128 124
ch 0 8 0 43 124 e p 75 62 43 119 124 65 101 45
ch 0 18 0 42 129 e p 123 129 106 42 67 117 113 61 62 87 124 122 76 82 93 47 120 77
ch 1 15 0 7 35 e p 21 30 12 28 19 27 16 35 34 18 9 35 7 10 18
ch 1 8 0 8 32 e p 9 8 29 30 27 32 21 13
ch 1 15 0 10 36 e p 22 13 17 12 17 23 10 35 29 34 26 22 36 11 13
ch 1 11 0 7 35 e p 9 35 21 25 31 7 17 10 23 31 16
ch 1 17 0 9 36 e p 16 26 17 10 11 11 17 24 18 31 36 9 30 25 13 23 23
qry
prd ge 0 51
prd ne 0 97
prj 1
end
""")


ORDER = sorted(CASES)


def prog(name):
    return CASES[name]
