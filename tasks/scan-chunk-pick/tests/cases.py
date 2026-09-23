"""The enumerated segment files: one per graded decision, and both sides of every fence.

Each name says which rule its file pins. The frozen answers are in `seal/gt.json`, and the
grader checks the sealed model still reproduces them before it grades anything, so a model
that had drifted cannot quietly redefine what these files mean.

Every file is written in the page grammar: a chunk line, then its pages. The files carried over
from the one-page-per-chunk design keep their intent with each chunk as a single page, and a
chunk that used to carry a literal token is a dictionary chunk whose page fell back to plain
values. The `pg-` files pin what pages change: a read of only the pages that need it, a
dictionary that speaks only for its index pages, and a keep verdict that still reads a page
holding a null. The `mem-` files pin the file's memory: nothing read twice, nothing charged
twice, a remembered page counting exactly from the start of a later query, and a page read by
a report pass serving the next query. The `hdr-` files pin the two sound header tests and the
widened bounds an inexact header stands for. The `dic-` files pin when a dictionary may decide, what each verdict does and that
a chunk's dictionary is charged once. The `ord-` files pin the choice: smallest expected
survivors, the cap by the chunk's survivors, the exact count of a chunk that has been read,
and the two tie-breaks. The `dec-` files pin what a read settles. The `prj-` files pin the
report pass. The rest fence the ordinary cases a wrong repair breaks: a query where nothing
prunes, a query that keeps everything, and two queries that must not share state.
"""

CASES = {}


def _add(name, text):
    CASES[name] = [ln for ln in text.strip("\n").split("\n")]

_add("dec-hits-whole-chunk", """
seg 10 8 3
ch 0 p
pg 8 0 5 9 e 56 v 5 5 5 5 9 9 9 9
ch 1 p
pg 4 0 0 0 e 0 v 0 0 0 0
ch 1 p
pg 4 0 1 1 e 4 v 1 1 1 1
ch 2 p
pg 8 0 1 8 e 36 v 1 2 3 4 5 6 7 8
qry
prd ge 0 6
prd le 1 0
prd eq 0 5
prd le 2 2
prj 2
end
""")

_add("del-caps-score", """
seg 10 6 2
ch 0 p
pg 3 0 0 9 e 14 v 0 5 9
ch 0 p
pg 3 0 1 20 e 25 v 1 4 20
ch 1 p
pg 6 0 1 6 e 21 v 1 2 3 4 5 6
del 0
del 1
qry
prd le 0 7
prj 1
end
""")

_add("del-never-alive", """
seg 10 6 2
ch 0 p
pg 3 0 1 3 e 6 v 1 2 3
ch 0 p
pg 3 0 4 6 e 15 v 4 5 6
ch 1 p
pg 6 0 1 6 e 21 v 1 2 3 4 5 6
del 0
del 1
del 2
qry
prd ge 0 2
prj 1
end
""")

_add("dic-charge-once", """
seg 10 8 2
ch 0 d 2 3 9
pg 4 0 3 9 e 24 i 0 1 0 1
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ne 0 5
prd ge 0 5
prj 1
end
""")

_add("dic-drop-with-nulls", """
seg 10 8 2
ch 0 d 2 3 9
pg 4 1 3 9 e 15 i 0 - 0 1
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd eq 0 5
prj 1
end
""")

_add("dic-not-for-null", """
seg 10 8 2
ch 0 d 2 3 9
pg 4 1 3 9 e 15 i 0 - 0 1
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd nn 0
prj 1
end
""")

_add("dic-nulls-read", """
seg 10 8 2
ch 0 d 2 3 9
pg 4 1 3 9 e 15 i 0 - 0 1
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ne 0 5
prj 1
end
""")

_add("dic-overflow-read", """
seg 10 8 2
ch 0 d 2 3 9
pg 4 0 3 9 e 22 v 3 7 3 9
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd eq 0 7
prj 1
end
""")

_add("dic-whole-drop", """
seg 10 8 2
ch 0 d 2 3 9
pg 4 0 3 9 e 24 i 0 1 0 1
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd eq 0 5
prj 1
end
""")

_add("dic-whole-keep", """
seg 10 8 2
ch 0 d 2 3 9
pg 4 0 3 9 e 24 i 0 1 0 1
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ne 0 5
prj 1
end
""")

_add("dic-whole-read", """
seg 10 8 2
ch 0 d 2 3 9
pg 4 0 3 9 e 24 i 0 1 0 1
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ge 0 5
prj 1
end
""")

_add("hdr-all-pass", """
seg 10 8 2
ch 0 p
pg 4 0 20 30 e 101 v 20 24 27 30
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ge 0 10
prj 1
end
""")

_add("hdr-miss-skip", """
seg 10 8 2
ch 0 p
pg 4 0 5 8 e 26 v 5 6 7 8
ch 0 p
pg 4 0 20 30 e 101 v 20 24 27 30
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ge 0 22
prj 1
end
""")

_add("hdr-ne-exact-miss", """
seg 10 8 2
ch 0 p
pg 4 0 7 7 e 28 v 7 7 7 7
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ne 0 7
prj 1
end
""")

_add("hdr-nu-no-nulls", """
seg 10 8 2
ch 0 p
pg 4 0 20 30 e 101 v 20 24 27 30
ch 0 p
pg 4 2 40 50 e 87 v 40 - 47 -
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd nu 0
prj 0
end
""")

_add("hdr-null-chunk-null", """
seg 10 8 2
ch 0 p
pg 4 4 - - e 0 v - - - -
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd nu 0
prj 1
end
qry
prd nn 0
prj 1
end
""")

_add("hdr-nulls-block-pass", """
seg 10 8 2
ch 0 p
pg 4 2 20 25 e 45 v 20 - 25 -
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ge 0 10
prj 1
end
""")

_add("hdr-widen-eq", """
seg 10 4 2
ch 0 p
pg 4 0 30 30 w 121 v 28 30 33 30
ch 1 p
pg 4 0 5 8 e 26 v 5 6 7 8
qry
prd eq 0 30
prj 0
end
""")

_add("hdr-widen-high", """
seg 10 4 2
ch 0 p
pg 4 0 30 40 w 143 v 21 34 48 40
ch 1 p
pg 4 0 5 8 e 26 v 5 6 7 8
qry
prd ge 0 45
prj 0
end
""")

_add("hdr-widen-low", """
seg 10 4 2
ch 0 p
pg 4 0 30 40 w 143 v 21 34 48 40
ch 1 p
pg 4 0 5 8 e 26 v 5 6 7 8
qry
prd le 0 25
prj 0
end
""")

_add("hdr-widen-ne", """
seg 10 4 2
ch 0 p
pg 4 0 30 30 w 121 v 28 30 33 30
ch 1 p
pg 4 0 5 8 e 26 v 5 6 7 8
qry
prd ne 0 30
prj 0
end
""")

_add("ord-exact-after-read", """
seg 10 8 2
ch 0 p
pg 8 0 10 17 e 87 v 10 10 10 10 10 10 10 17
ch 1 p
pg 4 0 0 3 e 6 v 0 1 2 3
ch 1 p
pg 4 0 0 3 e 6 v 0 1 2 3
qry
prd ge 0 15
prd eq 0 10
prd le 1 1
prj 1
end
""")

_add("ord-keeps-all", """
seg 10 8 2
ch 0 p
pg 4 0 20 30 e 101 v 20 24 27 30
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ge 0 5
prd le 1 9
prj 0 1
end
""")

_add("ord-nothing-prunes", """
seg 10 12 2
ch 0 p
pg 6 0 10 20 e 90 v 10 12 14 16 18 20
ch 0 p
pg 6 0 10 20 e 95 v 11 13 15 17 19 20
ch 1 p
pg 4 0 30 40 e 141 v 30 34 37 40
ch 1 p
pg 4 0 30 40 e 144 v 31 35 38 40
ch 1 p
pg 4 0 30 40 e 147 v 32 36 39 40
qry
prd ge 0 12
prd le 1 38
prj 0 1
end
""")

_add("ord-read-raises", """
seg 10 87 2
ch 0 p
pg 15 0 0 0 w 37 v 5 1 5 3 0 1 0 3 2 4 2 1 3 5 2
ch 0 d 6 0 1 2 3 4 5
pg 20 1 0 5 e 46 i 2 0 4 1 0 5 1 3 3 3 - 4 2 1 2 1 5 4 0 5
ch 0 d 6 0 1 2 3 4 5
pg 15 1 0 0 w 26 i 0 4 2 4 5 2 0 - 0 2 1 0 3 0 3
ch 0 d 4 1 2 3 5
pg 10 1 0 5 e 19 v 1 0 2 0 2 - 3 4 2 5
ch 0 d 6 0 1 2 3 4 5
pg 12 0 0 0 w 28 i 0 2 3 5 2 1 3 4 2 1 2 3
ch 0 p
pg 15 2 0 5 e 43 v 4 - 1 3 4 5 5 4 3 2 0 5 - 2 5
ch 1 d 6 0 1 2 3 4 5
pg 11 1 0 5 e 23 i 1 1 1 5 4 - 5 2 0 3 1
ch 1 d 6 0 1 2 3 4 5
pg 12 0 0 5 e 25 i 0 0 0 1 0 2 4 4 3 2 4 5
ch 1 d 6 0 1 2 3 4 5
pg 15 2 0 0 w 35 i 3 5 1 1 2 5 - 3 4 - 5 4 0 1 1
ch 1 d 4 0 2 3 4
pg 21 4 0 0 w 31 v 5 1 3 2 0 1 - 0 - - 0 4 2 0 5 1 0 2 2 3 -
ch 1 d 6 0 1 2 3 4 5
pg 18 0 0 0 w 45 i 2 2 0 4 2 2 5 0 5 3 1 5 2 5 4 1 2 0
ch 1 d 5 0 2 3 4 5
pg 10 1 0 5 e 31 i 4 1 4 0 4 3 1 2 4 -
qry
prd ge 1 0
prd ge 0 0
prd ge 0 1
prj 0
end
""")

_add("ord-read-rescored", """
seg 10 66 2
ch 0 p
pg 14 0 43 128 e 1082 v 123 107 121 112 128 53 58 60 55 65 49 59 43 49
ch 0 p
pg 15 0 41 112 e 1177 v 100 87 66 97 112 71 41 49 98 59 42 102 73 108 72
ch 0 p
pg 11 0 51 128 e 962 v 97 78 52 93 64 92 106 77 51 128 124
ch 0 p
pg 8 0 43 124 e 634 v 75 62 43 119 124 65 101 45
ch 0 p
pg 18 0 42 129 e 1648 v 123 129 106 42 67 117 113 61 62 87 124 122 76 82 93 47 120 77
ch 1 p
pg 15 0 7 35 e 319 v 21 30 12 28 19 27 16 35 34 18 9 35 7 10 18
ch 1 p
pg 8 0 8 32 e 169 v 9 8 29 30 27 32 21 13
ch 1 p
pg 15 0 10 36 e 320 v 22 13 17 12 17 23 10 35 29 34 26 22 36 11 13
ch 1 p
pg 11 0 7 35 e 225 v 9 35 21 25 31 7 17 10 23 31 16
ch 1 p
pg 17 0 9 36 e 340 v 16 26 17 10 11 11 17 24 18 31 36 9 30 25 13 23 23
qry
prd ge 0 51
prd ne 0 97
prj 1
end
""")

_add("ord-spread-rounds-up", """
seg 10 4 2
ch 0 p
pg 4 0 3 9 e 24 v 3 5 7 9
ch 1 p
pg 2 0 0 1 e 1 v 0 1
ch 1 p
pg 2 0 0 1 e 1 v 0 1
qry
prd eq 1 1
prd eq 0 5
prj 0
end
""")

_add("ord-spread-takes-edge", """
seg 10 4 2
ch 0 p
pg 4 0 3 9 e 24 v 3 5 7 9
ch 1 p
pg 2 0 0 1 e 1 v 0 1
ch 1 p
pg 2 0 0 1 e 1 v 0 1
qry
prd eq 1 1
prd ge 0 9
prj 0
end
""")

_add("prj-dead-chunk", """
seg 10 8 2
ch 0 p
pg 4 0 5 8 e 26 v 5 6 7 8
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 4 0 1 2 e 6 v 1 2 1 2
ch 1 p
pg 4 0 3 4 e 14 v 3 4 3 4
qry
prd ge 0 20
prj 1
end
""")

_add("prj-listed-order", """
seg 10 4 3
ch 0 p
pg 4 0 20 30 e 101 v 20 24 27 30
ch 1 p
pg 4 0 1 2 e 6 v 1 2 1 2
ch 2 p
pg 4 0 7 8 e 30 v 7 8 7 8
qry
prd ge 0 10
prj 2 1
end
""")

_add("prj-moved-no-read", """
seg 10 4 2
ch 0 p
pg 4 0 1 4 e 10 v 1 2 3 4
ch 1 p
pg 2 0 10 20 e 30 v 10 20
ch 1 p
pg 2 0 30 40 e 70 v 30 40
up 1 0 7
up 1 1 -
qry
prd ge 0 1
prj 1
end
""")

_add("prj-nulls-out", """
seg 10 4 2
ch 0 p
pg 4 0 20 30 e 101 v 20 24 27 30
ch 1 p
pg 4 2 1 2 e 3 v 1 - 2 -
qry
prd ge 0 10
prj 1
end
""")

_add("prj-one-entry-nulls", """
seg 10 4 2
ch 0 p
pg 4 0 1 9 e 15 v 1 9 2 3
ch 1 d 1 20
pg 2 1 20 20 w 20 i 0 -
ch 1 p
pg 2 0 30 40 e 70 v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-one-entry-rd", """
seg 10 4 2
ch 0 p
pg 4 0 1 9 e 15 v 1 9 2 3
ch 1 d 1 20
pg 2 0 20 20 w 40 i 0 0
ch 1 p
pg 2 0 30 40 e 70 v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-pinned-no-read", """
seg 10 4 2
ch 0 p
pg 4 0 1 9 e 15 v 1 9 2 3
ch 1 p
pg 2 0 12 12 e 24 v 12 12
ch 1 p
pg 2 0 30 40 e 70 v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-reuse-read", """
seg 10 4 2
ch 0 p
pg 4 1 20 30 e 77 v 20 - 27 30
ch 1 p
pg 4 0 1 2 e 6 v 1 2 1 2
qry
prd ge 0 22
prj 0
end
""")

_add("prj-same-twice", """
seg 10 4 2
ch 0 p
pg 4 0 20 30 e 101 v 20 24 27 30
ch 1 p
pg 4 0 1 2 e 6 v 1 2 1 2
qry
prd ge 0 10
prj 1 1
end
""")

_add("prj-void-no-read", """
seg 10 4 2
ch 0 p
pg 4 0 1 9 e 15 v 1 9 2 3
ch 1 p
pg 2 2 - - e 0 v - -
ch 1 p
pg 2 0 30 40 e 70 v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-widened-not-pinned", """
seg 10 4 2
ch 0 p
pg 4 0 1 9 e 15 v 1 9 2 3
ch 1 p
pg 2 0 20 20 w 40 v 20 20
ch 1 p
pg 2 0 30 40 e 70 v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("qry-starts-over", """
seg 10 8 2
ch 0 d 2 3 9
pg 4 0 3 9 e 24 i 0 1 0 1
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
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
ch 0 p
pg 4 0 5 8 e 26 v 5 6 7 8
ch 0 p
pg 4 0 40 50 e 181 v 40 44 47 50
ch 1 p
pg 8 0 1 2 e 12 v 1 2 1 2 1 2 1 2
qry
prd ge 0 60
prj 0 1
end
""")

_add("upd-all-moved-no-rd", """
seg 10 6 2
ch 0 d 3 0 5 9
pg 3 0 0 9 e 14 i 0 1 2
ch 0 p
pg 3 0 0 9 e 15 v 1 6 8
ch 1 p
pg 6 0 1 6 e 21 v 1 2 3 4 5 6
up 0 0 7
up 0 1 2
up 0 2 9
qry
prd ge 0 5
prj 1
end
""")

_add("upd-all-moved-no-read", """
seg 10 6 2
ch 0 p
pg 3 0 0 9 e 14 v 0 5 9
ch 0 p
pg 3 0 0 9 e 15 v 1 6 8
ch 1 p
pg 6 0 1 6 e 21 v 1 2 3 4 5 6
up 0 0 7
up 0 1 2
up 0 2 9
qry
prd ge 0 5
prj 1
end
""")

_add("upd-count-as-written", """
seg 25 134 2
ch 0 p
pg 23 21 1 2 e 3 v - - - - - - - - - - - - - 2 - - - - - - - 1 -
ch 0 d 3 1 2 5
pg 24 19 1 5 e 14 i 2 - - - - 2 - - 0 - 1 - 0 - - - - - - - - - - -
ch 0 d 1 1
pg 29 28 1 1 e 1 i - - - - - - - - - 0 - - - - - - - - - - - - - - - - - - -
ch 0 p
pg 23 23 - - e 0 v - - - - - - - - - - - - - - - - - - - - - - -
ch 0 d 2 2 3
pg 35 32 2 3 e 7 i 0 - - - - - - - - - - - - - - - - - - - - 0 - - - - - - 1 - - - - - -
ch 1 p
pg 21 19 7 8 e 15 v 7 - - - - - 8 - - - - - - - - - - - - - -
ch 1 p
pg 33 31 2 11 e 13 v - - - - - - - - - - - - - - 11 - - - - - - - - - - - - - - - - 2 -
ch 1 d 2 6 11
pg 16 14 6 11 e 17 i - - - - 1 - 0 - - - - - - - - -
ch 1 d 2 0 4
pg 27 24 0 0 w 8 i - - - - - - - - - - - - 1 - - - - - - - - - - 1 0 - -
ch 1 d 2 6 10
pg 37 35 6 10 e 16 i - - - - - - 1 - - - - - - - 0 - - - - - - - - - - - - - - - - - - - - - -
up 1 38 8
up 1 41 0
qry
prd nn 1
prd nu 0
prd ge 1 2
prj 1
end
""")

_add("upd-drop-spares", """
seg 10 4 2
ch 0 p
pg 4 0 5 8 e 26 v 5 6 7 8
ch 1 p
pg 4 0 1 4 e 10 v 1 2 3 4
up 0 1 30
qry
prd ge 0 20
prj 1 0
end
""")

_add("upd-keep-tests", """
seg 10 4 2
ch 0 p
pg 4 0 5 8 e 26 v 5 6 7 8
ch 1 p
pg 4 0 1 4 e 10 v 1 2 3 4
up 0 2 1
qry
prd ge 0 3
prj 1
end
""")

_add("upd-last-held-dies", """
seg 10 6 2
ch 0 p
pg 6 0 1 6 e 21 v 1 2 3 4 5 6
ch 1 p
pg 3 0 0 9 e 14 v 0 5 9
ch 1 p
pg 3 0 0 9 e 15 v 1 6 8
up 1 0 7
up 1 1 2
qry
prd le 0 2
prd ge 1 5
prj 0
end
""")

_add("pg-partial-read", """
seg 10 9 2
ch 0 p
pg 3 0 1 3 e 6 v 1 2 3
pg 3 0 5 12 e 26 v 5 9 12
pg 3 0 20 30 e 75 v 20 25 30
ch 1 p
pg 9 0 1 9 e 45 v 1 2 3 4 5 6 7 8 9
qry
prd ge 0 10
prj 1
end
""")

_add("pg-dict-skips-fallback", """
seg 10 7 2
ch 0 d 3 3 4 12
pg 4 0 3 12 e 22 i 0 1 0 2
pg 3 0 3 8 e 15 v 3 8 4
ch 1 p
pg 7 0 1 7 e 28 v 1 2 3 4 5 6 7
qry
prd eq 0 8
prj 1
end
""")

_add("pg-dict-keep-page-nulls", """
seg 10 4 2
ch 0 d 2 20 30
pg 2 0 20 30 w 50 i 0 1
pg 2 1 30 30 w 30 i 1 -
ch 1 p
pg 4 0 1 4 e 10 v 1 2 3 4
qry
prd ge 0 15
prj 1
end
""")

_add("mem-no-reread", """
seg 10 6 2
ch 0 p
pg 3 0 1 9 e 15 v 1 5 9
pg 3 0 2 8 e 16 v 2 6 8
ch 1 p
pg 6 0 1 6 e 21 v 1 2 3 4 5 6
qry
prd ge 0 5
prj 1
end
qry
prd le 0 6
prj 1
end
""")

_add("mem-exact-from-start", """
seg 10 6 2
ch 0 p
pg 3 0 50 70 w 180 v 50 60 70
ch 0 p
pg 3 0 60 80 e 210 v 60 70 80
ch 1 p
pg 3 0 7 9 e 24 v 7 8 9
ch 1 p
pg 3 0 1 3 e 6 v 1 2 3
qry
prd ge 0 55
prj 0
end
qry
prd eq 1 8
prd le 0 45
prj 1
end
""")

_add("mem-charge-once-file", """
seg 10 6 2
ch 0 d 3 2 5 8
pg 6 0 2 8 e 30 i 0 1 2 0 1 2
ch 1 p
pg 6 0 1 6 e 21 v 1 2 3 4 5 6
qry
prd ge 0 3
prj 1
end
qry
prd le 0 6
prj 1
end
""")

_add("mem-report-read-kept", """
seg 10 6 2
ch 0 p
pg 6 0 1 6 e 21 v 1 2 3 4 5 6
ch 1 p
pg 6 0 10 60 e 210 v 10 20 30 40 50 60
qry
prd le 0 4
prj 1
end
qry
prd ge 1 25
prj 0
end
""")

_add("prj-whole-page-sum", """
seg 10 6 2
ch 0 p
pg 3 0 1 3 e 6 v 1 2 3
pg 3 0 7 9 e 24 v 7 8 9
ch 1 p
pg 3 0 10 30 e 60 v 10 20 30
pg 3 1 40 60 e 100 v 40 - 60
qry
prd ge 0 5
prj 1
end
""")

_add("prj-whole-broken-by-delete", """
seg 10 6 2
ch 0 p
pg 3 0 1 3 e 6 v 1 2 3
pg 3 0 7 9 e 24 v 7 8 9
ch 1 p
pg 3 0 10 30 e 60 v 10 20 30
pg 3 1 40 60 e 100 v 40 - 60
del 4
qry
prd ge 0 5
prj 1
end
""")

_add("prj-whole-broken-by-update", """
seg 10 6 2
ch 0 p
pg 3 0 1 3 e 6 v 1 2 3
pg 3 0 7 9 e 24 v 7 8 9
ch 1 p
pg 3 0 10 30 e 60 v 10 20 30
pg 3 1 40 60 e 100 v 40 - 60
up 1 5 99
qry
prd ge 0 5
prj 1
end
""")

_add("prj-one-entry-fallback", """
seg 10 4 2
ch 0 p
pg 4 0 1 4 e 10 v 1 2 3 4
ch 1 d 1 20
pg 2 0 20 20 w 40 i 0 0
pg 2 0 20 20 w 40 v 20 20
qry
prd le 0 3
prj 1
end
""")

_add("pg-count-mixed", """
seg 10 6 2
ch 0 p
pg 2 0 50 60 w 110 v 50 60
pg 1 0 70 70 e 70 v 70
ch 0 p
pg 3 0 60 80 e 210 v 60 70 80
ch 1 p
pg 3 0 7 9 e 24 v 7 8 9
ch 1 p
pg 3 0 1 3 e 6 v 1 2 3
qry
prd ge 0 55
prj 0
end
qry
prd eq 1 8
prd le 0 45
prj 1
end
""")

_add("mem-charge-across", """
seg 10 6 2
ch 0 d 2 2 9
pg 6 0 2 9 e 33 i 0 1 0 1 0 1
ch 1 p
pg 6 0 1 6 e 21 v 1 2 3 4 5 6
qry
prd eq 0 5
prj 1
end
qry
prd ne 0 5
prj 1
end
""")


ORDER = sorted(CASES)


def prog(name):
    return CASES[name]
