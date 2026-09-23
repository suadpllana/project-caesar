"""The enumerated segment files: one per graded decision, and both sides of every fence.

Each name says which rule its file pins. The frozen answers are in `seal/gt.json`, and the
grader checks the sealed model still reproduces them before it grades anything, so a model
that had drifted cannot quietly redefine what these files mean.

Every file is written in the page grammar: a chunk line carrying its sum, then its pages. The
`flt-` files pin that what is known acts at once and on every condition: a header, a remembered
page, an updated value or a consulted dictionary kills a row before any pair is applied or as
soon as it is learned, including rows of pages the pair was not reading. The `pg-` files pin
what pages change: a read of only the pages that need it, a dictionary that speaks only for its
index pages, and a keep verdict that still reads a page holding a null. The `mem-` files pin
the file's memory. The `hdr-` files pin the two sound header tests and the widened bounds an
inexact header stands for. The `dic-` files pin when a dictionary may decide, what each verdict
does and that a chunk's dictionary is charged once. The `ord-` files pin the choice: smallest
expected survivors, the cap by the chunk's survivors, the exact count of a page that has been
read, a score that a read raises, and the two tie-breaks. The `dec-` files pin what a read
settles. The `prj-` files pin the report pass: a chunk's sum answering its wholly live pages
together, a dead page with an unknown sum blocking that, a one-value page holding nulls whose
sum is known all the same, reads in page order, and the one-entry dictionary consulted only
when that spares a read and only for a live row. The rest fence the ordinary cases a wrong
repair breaks: a query where nothing prunes, a query that keeps everything, and two queries
that must not share state.

In every file the sums, null counts, recorded pairs and indexes are what the values give.
"""

CASES = {}


def _add(name, text):
    CASES[name] = [ln for ln in text.strip("\n").split("\n")]

_add("dec-hits-whole-chunk", """
seg 10 8 3
ch 0 p 56
pg 8 0 5 9 e v 5 5 5 5 9 9 9 9
ch 1 p 0
pg 4 0 0 0 e v 0 0 0 0
ch 1 p 4
pg 4 0 1 1 e v 1 1 1 1
ch 2 p 36
pg 8 0 1 8 e v 1 2 3 4 5 6 7 8
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
ch 0 p 14
pg 3 0 0 9 e v 0 5 9
ch 0 p 25
pg 3 0 1 20 e v 1 4 20
ch 1 p 21
pg 6 0 1 6 e v 1 2 3 4 5 6
del 0
del 1
qry
prd le 0 7
prj 1
end
""")

_add("del-never-alive", """
seg 10 6 2
ch 0 p 6
pg 3 0 1 3 e v 1 2 3
ch 0 p 15
pg 3 0 4 6 e v 4 5 6
ch 1 p 21
pg 6 0 1 6 e v 1 2 3 4 5 6
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
ch 0 d 24 2 3 9
pg 4 0 3 9 e i 0 1 0 1
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ne 0 5
prd ge 0 5
prj 1
end
""")

_add("dic-drop-with-nulls", """
seg 10 8 2
ch 0 d 15 2 3 9
pg 4 1 3 9 e i 0 - 0 1
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd eq 0 5
prj 1
end
""")

_add("dic-not-for-null", """
seg 10 8 2
ch 0 d 15 2 3 9
pg 4 1 3 9 e i 0 - 0 1
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd nn 0
prj 1
end
""")

_add("dic-nulls-read", """
seg 10 8 2
ch 0 d 15 2 3 9
pg 4 1 3 9 e i 0 - 0 1
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ne 0 5
prj 1
end
""")

_add("dic-overflow-read", """
seg 10 8 2
ch 0 d 22 2 3 9
pg 4 0 3 9 e v 3 7 3 9
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd eq 0 7
prj 1
end
""")

_add("dic-whole-drop", """
seg 10 8 2
ch 0 d 24 2 3 9
pg 4 0 3 9 e i 0 1 0 1
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd eq 0 5
prj 1
end
""")

_add("dic-whole-keep", """
seg 10 8 2
ch 0 d 24 2 3 9
pg 4 0 3 9 e i 0 1 0 1
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ne 0 5
prj 1
end
""")

_add("dic-whole-read", """
seg 10 8 2
ch 0 d 24 2 3 9
pg 4 0 3 9 e i 0 1 0 1
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ge 0 5
prj 1
end
""")

_add("hdr-all-pass", """
seg 10 8 2
ch 0 p 101
pg 4 0 20 30 e v 20 24 27 30
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ge 0 10
prj 1
end
""")

_add("hdr-miss-skip", """
seg 10 8 2
ch 0 p 26
pg 4 0 5 8 e v 5 6 7 8
ch 0 p 101
pg 4 0 20 30 e v 20 24 27 30
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ge 0 22
prj 1
end
""")

_add("hdr-ne-exact-miss", """
seg 10 8 2
ch 0 p 28
pg 4 0 7 7 e v 7 7 7 7
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ne 0 7
prj 1
end
""")

_add("hdr-nu-no-nulls", """
seg 10 8 2
ch 0 p 101
pg 4 0 20 30 e v 20 24 27 30
ch 0 p 87
pg 4 2 40 47 e v 40 - 47 -
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd nu 0
prj 0
end
""")

_add("hdr-null-chunk-null", """
seg 10 8 2
ch 0 p 0
pg 4 4 - - e v - - - -
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
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
ch 0 p 45
pg 4 2 20 25 e v 20 - 25 -
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ge 0 10
prj 1
end
""")

_add("hdr-widen-eq", """
seg 10 4 2
ch 0 p 121
pg 4 0 30 30 w v 28 30 33 30
ch 1 p 26
pg 4 0 5 8 e v 5 6 7 8
qry
prd eq 0 30
prj 0
end
""")

_add("hdr-widen-high", """
seg 10 4 2
ch 0 p 143
pg 4 0 30 40 w v 21 34 48 40
ch 1 p 26
pg 4 0 5 8 e v 5 6 7 8
qry
prd ge 0 45
prj 0
end
""")

_add("hdr-widen-low", """
seg 10 4 2
ch 0 p 143
pg 4 0 30 40 w v 21 34 48 40
ch 1 p 26
pg 4 0 5 8 e v 5 6 7 8
qry
prd le 0 25
prj 0
end
""")

_add("hdr-widen-ne", """
seg 10 4 2
ch 0 p 121
pg 4 0 30 30 w v 28 30 33 30
ch 1 p 26
pg 4 0 5 8 e v 5 6 7 8
qry
prd ne 0 30
prj 0
end
""")

_add("ord-exact-after-read", """
seg 10 8 2
ch 0 p 87
pg 8 0 10 17 e v 10 10 10 10 10 10 10 17
ch 1 p 6
pg 4 0 0 3 e v 0 1 2 3
ch 1 p 6
pg 4 0 0 3 e v 0 1 2 3
qry
prd ge 0 15
prd eq 0 10
prd le 1 1
prj 1
end
""")

_add("ord-keeps-all", """
seg 10 8 2
ch 0 p 101
pg 4 0 20 30 e v 20 24 27 30
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ge 0 5
prd le 1 9
prj 0 1
end
""")

_add("ord-nothing-prunes", """
seg 10 12 2
ch 0 p 90
pg 6 0 10 20 e v 10 12 14 16 18 20
ch 0 p 95
pg 6 0 11 20 e v 11 13 15 17 19 20
ch 1 p 141
pg 4 0 30 40 e v 30 34 37 40
ch 1 p 144
pg 4 0 31 40 e v 31 35 38 40
ch 1 p 147
pg 4 0 32 40 e v 32 36 39 40
qry
prd ge 0 12
prd le 1 38
prj 0 1
end
""")

_add("ord-read-raises", """
seg 10 87 2
ch 0 p 37
pg 15 0 0 0 w v 5 1 5 3 0 1 0 3 2 4 2 1 3 5 2
ch 0 d 46 6 0 1 2 3 4 5
pg 20 1 0 5 e i 2 0 4 1 0 5 1 3 3 3 - 4 2 1 2 1 5 4 0 5
ch 0 d 26 6 0 1 2 3 4 5
pg 15 1 0 0 w i 0 4 2 4 5 2 0 - 0 2 1 0 3 0 3
ch 0 d 19 4 1 2 3 5
pg 10 1 0 5 e v 1 0 2 0 2 - 3 4 2 5
ch 0 d 28 6 0 1 2 3 4 5
pg 12 0 0 0 w i 0 2 3 5 2 1 3 4 2 1 2 3
ch 0 p 43
pg 15 2 0 5 e v 4 - 1 3 4 5 5 4 3 2 0 5 - 2 5
ch 1 d 23 6 0 1 2 3 4 5
pg 11 1 0 5 e i 1 1 1 5 4 - 5 2 0 3 1
ch 1 d 25 6 0 1 2 3 4 5
pg 12 0 0 5 e i 0 0 0 1 0 2 4 4 3 2 4 5
ch 1 d 35 6 0 1 2 3 4 5
pg 15 2 0 0 w i 3 5 1 1 2 5 - 3 4 - 5 4 0 1 1
ch 1 d 31 4 0 2 3 4
pg 21 4 0 0 w v 5 1 3 2 0 1 - 0 - - 0 4 2 0 5 1 0 2 2 3 -
ch 1 d 45 6 0 1 2 3 4 5
pg 18 0 0 0 w i 2 2 0 4 2 2 5 0 5 3 1 5 2 5 4 1 2 0
ch 1 d 31 5 0 2 3 4 5
pg 10 1 0 5 e i 4 1 4 0 4 3 1 2 4 -
qry
prd ge 1 0
prd ge 0 0
prd ge 0 1
prj 0
end
""")

_add("ord-read-rescored", """
seg 10 66 2
ch 0 p 1082
pg 14 0 43 128 e v 123 107 121 112 128 53 58 60 55 65 49 59 43 49
ch 0 p 1177
pg 15 0 41 112 e v 100 87 66 97 112 71 41 49 98 59 42 102 73 108 72
ch 0 p 962
pg 11 0 51 128 e v 97 78 52 93 64 92 106 77 51 128 124
ch 0 p 634
pg 8 0 43 124 e v 75 62 43 119 124 65 101 45
ch 0 p 1648
pg 18 0 42 129 e v 123 129 106 42 67 117 113 61 62 87 124 122 76 82 93 47 120 77
ch 1 p 319
pg 15 0 7 35 e v 21 30 12 28 19 27 16 35 34 18 9 35 7 10 18
ch 1 p 169
pg 8 0 8 32 e v 9 8 29 30 27 32 21 13
ch 1 p 320
pg 15 0 10 36 e v 22 13 17 12 17 23 10 35 29 34 26 22 36 11 13
ch 1 p 225
pg 11 0 7 35 e v 9 35 21 25 31 7 17 10 23 31 16
ch 1 p 340
pg 17 0 9 36 e v 16 26 17 10 11 11 17 24 18 31 36 9 30 25 13 23 23
qry
prd ge 0 51
prd ne 0 97
prj 1
end
""")

_add("ord-spread-rounds-up", """
seg 10 4 2
ch 0 p 24
pg 4 0 3 9 e v 3 5 7 9
ch 1 p 1
pg 2 0 0 1 e v 0 1
ch 1 p 1
pg 2 0 0 1 e v 0 1
qry
prd eq 1 1
prd eq 0 5
prj 0
end
""")

_add("ord-spread-takes-edge", """
seg 10 4 2
ch 0 p 24
pg 4 0 3 9 e v 3 5 7 9
ch 1 p 1
pg 2 0 0 1 e v 0 1
ch 1 p 1
pg 2 0 0 1 e v 0 1
qry
prd eq 1 1
prd ge 0 9
prj 0
end
""")

_add("prj-dead-chunk", """
seg 10 8 2
ch 0 p 26
pg 4 0 5 8 e v 5 6 7 8
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 6
pg 4 0 1 2 e v 1 2 1 2
ch 1 p 14
pg 4 0 3 4 e v 3 4 3 4
qry
prd ge 0 20
prj 1
end
""")

_add("prj-listed-order", """
seg 10 4 3
ch 0 p 101
pg 4 0 20 30 e v 20 24 27 30
ch 1 p 6
pg 4 0 1 2 e v 1 2 1 2
ch 2 p 30
pg 4 0 7 8 e v 7 8 7 8
qry
prd ge 0 10
prj 2 1
end
""")

_add("prj-moved-no-read", """
seg 10 4 2
ch 0 p 10
pg 4 0 1 4 e v 1 2 3 4
ch 1 p 30
pg 2 0 10 20 e v 10 20
ch 1 p 70
pg 2 0 30 40 e v 30 40
up 1 0 7
up 1 1 -
qry
prd ge 0 1
prj 1
end
""")

_add("prj-nulls-out", """
seg 10 4 2
ch 0 p 101
pg 4 0 20 30 e v 20 24 27 30
ch 1 p 3
pg 4 2 1 2 e v 1 - 2 -
qry
prd ge 0 10
prj 1
end
""")

_add("prj-one-entry-nulls", """
seg 10 4 2
ch 0 p 15
pg 4 0 1 9 e v 1 9 2 3
ch 1 d 20 1 20
pg 2 1 20 20 w i 0 -
ch 1 p 70
pg 2 0 30 40 e v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-one-entry-rd", """
seg 10 4 2
ch 0 p 15
pg 4 0 1 9 e v 1 9 2 3
ch 1 d 40 1 20
pg 2 0 20 20 w i 0 0
ch 1 p 70
pg 2 0 30 40 e v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-pinned-no-read", """
seg 10 4 2
ch 0 p 15
pg 4 0 1 9 e v 1 9 2 3
ch 1 p 24
pg 2 0 12 12 e v 12 12
ch 1 p 70
pg 2 0 30 40 e v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-reuse-read", """
seg 10 4 2
ch 0 p 77
pg 4 1 20 30 e v 20 - 27 30
ch 1 p 6
pg 4 0 1 2 e v 1 2 1 2
qry
prd ge 0 22
prj 0
end
""")

_add("prj-same-twice", """
seg 10 4 2
ch 0 p 101
pg 4 0 20 30 e v 20 24 27 30
ch 1 p 6
pg 4 0 1 2 e v 1 2 1 2
qry
prd ge 0 10
prj 1 1
end
""")

_add("prj-void-no-read", """
seg 10 4 2
ch 0 p 15
pg 4 0 1 9 e v 1 9 2 3
ch 1 p 0
pg 2 2 - - e v - -
ch 1 p 70
pg 2 0 30 40 e v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("prj-widened-not-pinned", """
seg 10 4 2
ch 0 p 15
pg 4 0 1 9 e v 1 9 2 3
ch 1 p 40
pg 2 0 20 20 w v 20 20
ch 1 p 70
pg 2 0 30 40 e v 30 40
qry
prd le 0 3
prj 1
end
""")

_add("qry-starts-over", """
seg 10 8 2
ch 0 d 24 2 3 9
pg 4 0 3 9 e i 0 1 0 1
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
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
ch 0 p 26
pg 4 0 5 8 e v 5 6 7 8
ch 0 p 181
pg 4 0 40 50 e v 40 44 47 50
ch 1 p 12
pg 8 0 1 2 e v 1 2 1 2 1 2 1 2
qry
prd ge 0 60
prj 0 1
end
""")

_add("upd-all-moved-no-rd", """
seg 10 6 2
ch 0 d 14 3 0 5 9
pg 3 0 0 9 e i 0 1 2
ch 0 p 15
pg 3 0 1 8 e v 1 6 8
ch 1 p 21
pg 6 0 1 6 e v 1 2 3 4 5 6
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
ch 0 p 14
pg 3 0 0 9 e v 0 5 9
ch 0 p 15
pg 3 0 1 8 e v 1 6 8
ch 1 p 21
pg 6 0 1 6 e v 1 2 3 4 5 6
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
ch 0 p 3
pg 23 21 1 2 e v - - - - - - - - - - - - - 2 - - - - - - - 1 -
ch 0 d 14 3 1 2 5
pg 24 19 1 5 e i 2 - - - - 2 - - 0 - 1 - 0 - - - - - - - - - - -
ch 0 d 1 1 1
pg 29 28 1 1 e i - - - - - - - - - 0 - - - - - - - - - - - - - - - - - - -
ch 0 p 0
pg 23 23 - - e v - - - - - - - - - - - - - - - - - - - - - - -
ch 0 d 7 2 2 3
pg 35 32 2 3 e i 0 - - - - - - - - - - - - - - - - - - - - 0 - - - - - - 1 - - - - - -
ch 1 p 15
pg 21 19 7 8 e v 7 - - - - - 8 - - - - - - - - - - - - - -
ch 1 p 13
pg 33 31 2 11 e v - - - - - - - - - - - - - - 11 - - - - - - - - - - - - - - - - 2 -
ch 1 d 17 2 6 11
pg 16 14 6 11 e i - - - - 1 - 0 - - - - - - - - -
ch 1 d 8 2 0 4
pg 27 24 0 0 w i - - - - - - - - - - - - 1 - - - - - - - - - - 1 0 - -
ch 1 d 16 2 6 10
pg 37 35 6 10 e i - - - - - - 1 - - - - - - - 0 - - - - - - - - - - - - - - - - - - - - - -
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
ch 0 p 26
pg 4 0 5 8 e v 5 6 7 8
ch 1 p 10
pg 4 0 1 4 e v 1 2 3 4
up 0 1 30
qry
prd ge 0 20
prj 1 0
end
""")

_add("upd-keep-tests", """
seg 10 4 2
ch 0 p 26
pg 4 0 5 8 e v 5 6 7 8
ch 1 p 10
pg 4 0 1 4 e v 1 2 3 4
up 0 2 1
qry
prd ge 0 3
prj 1
end
""")

_add("upd-last-held-dies", """
seg 10 6 2
ch 0 p 21
pg 6 0 1 6 e v 1 2 3 4 5 6
ch 1 p 14
pg 3 0 0 9 e v 0 5 9
ch 1 p 15
pg 3 0 1 8 e v 1 6 8
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
ch 0 p 107
pg 3 0 1 3 e v 1 2 3
pg 3 0 5 12 e v 5 9 12
pg 3 0 20 30 e v 20 25 30
ch 1 p 45
pg 9 0 1 9 e v 1 2 3 4 5 6 7 8 9
qry
prd ge 0 10
prj 1
end
""")

_add("pg-dict-skips-fallback", """
seg 10 7 2
ch 0 d 37 3 3 4 12
pg 4 0 3 12 e i 0 1 0 2
pg 3 0 3 8 e v 3 8 4
ch 1 p 28
pg 7 0 1 7 e v 1 2 3 4 5 6 7
qry
prd eq 0 8
prj 1
end
""")

_add("pg-dict-keep-page-nulls", """
seg 10 4 2
ch 0 d 80 2 20 30
pg 2 0 20 30 w i 0 1
pg 2 1 30 30 w i 1 -
ch 1 p 10
pg 4 0 1 4 e v 1 2 3 4
qry
prd ge 0 15
prj 1
end
""")

_add("mem-no-reread", """
seg 10 6 2
ch 0 p 31
pg 3 0 1 9 e v 1 5 9
pg 3 0 2 8 e v 2 6 8
ch 1 p 21
pg 6 0 1 6 e v 1 2 3 4 5 6
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
ch 0 p 180
pg 3 0 50 70 w v 50 60 70
ch 0 p 210
pg 3 0 60 80 e v 60 70 80
ch 1 p 24
pg 3 0 7 9 e v 7 8 9
ch 1 p 6
pg 3 0 1 3 e v 1 2 3
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
ch 0 d 30 3 2 5 8
pg 6 0 2 8 e i 0 1 2 0 1 2
ch 1 p 21
pg 6 0 1 6 e v 1 2 3 4 5 6
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
ch 0 p 21
pg 6 0 1 6 e v 1 2 3 4 5 6
ch 1 p 210
pg 6 0 10 60 e v 10 20 30 40 50 60
qry
prd le 0 4
prj 1
end
qry
prd ge 1 25
prj 0
end
""")

_add("prj-dead-page-blocks-sum", """
seg 10 6 2
ch 0 p 30
pg 3 0 1 3 e v 1 2 3
pg 3 0 7 9 e v 7 8 9
ch 1 p 160
pg 3 0 10 30 e v 10 20 30
pg 3 1 40 60 e v 40 - 60
qry
prd ge 0 5
prj 1
end
""")

_add("prj-whole-broken-by-delete", """
seg 10 6 2
ch 0 p 30
pg 3 0 1 3 e v 1 2 3
pg 3 0 7 9 e v 7 8 9
ch 1 p 160
pg 3 0 10 30 e v 10 20 30
pg 3 1 40 60 e v 40 - 60
del 4
qry
prd ge 0 5
prj 1
end
""")

_add("prj-whole-broken-by-update", """
seg 10 6 2
ch 0 p 30
pg 3 0 1 3 e v 1 2 3
pg 3 0 7 9 e v 7 8 9
ch 1 p 160
pg 3 0 10 30 e v 10 20 30
pg 3 1 40 60 e v 40 - 60
up 1 5 99
qry
prd ge 0 5
prj 1
end
""")

_add("prj-one-entry-fallback", """
seg 10 4 2
ch 0 p 10
pg 4 0 1 4 e v 1 2 3 4
ch 1 d 80 1 20
pg 2 0 20 20 w i 0 0
pg 2 0 20 20 w v 20 20
qry
prd le 0 3
prj 1
end
""")

_add("pg-count-mixed", """
seg 10 6 2
ch 0 p 180
pg 2 0 50 60 w v 50 60
pg 1 0 70 70 e v 70
ch 0 p 210
pg 3 0 60 80 e v 60 70 80
ch 1 p 24
pg 3 0 7 9 e v 7 8 9
ch 1 p 6
pg 3 0 1 3 e v 1 2 3
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
ch 0 d 33 2 2 9
pg 6 0 2 9 e i 0 1 0 1 0 1
ch 1 p 21
pg 6 0 1 6 e v 1 2 3 4 5 6
qry
prd eq 0 5
prj 1
end
qry
prd ne 0 5
prj 1
end
""")


_add("flt-header-kills-at-start", """
seg 10 5 1
ch 0 p 15
pg 3 0 2 7 e v 7 2 6
pg 2 2 - - e v - -
qry
prd ge 0 4
prd nu 0
prj 0
end
""")

_add("flt-header-kills-other-column", """
seg 10 9 2
ch 0 p 10
pg 3 0 1 5 e v 4 1 5
ch 0 p 39
pg 6 0 4 9 e v 4 5 6 7 8 9
ch 1 p 36
pg 3 0 0 0 e v 0 0 0
pg 6 0 1 9 e v 5 6 7 8 9 1
qry
prd ge 0 4
prd ge 1 5
prj 1
end
""")

_add("flt-memory-kills-at-start", """
seg 10 7 2
ch 0 p 29
pg 2 0 11 18 e v 18 11
ch 0 p 15
pg 2 1 15 15 e v - 15
ch 0 p 58
pg 1 0 16 16 e v 16
pg 2 0 16 26 e v 16 26
ch 1 d 260 5 40 41 42 45 46
pg 1 0 40 40 e i 0
pg 3 0 41 45 e i 2 1 3
pg 3 1 46 46 e i - 4 4
qry
prd ne 1 41
prj 0
end
qry
prd ge 1 43
prd le 0 15
prj 1
end
""")

_add("flt-dict-settles-every-page", """
seg 5 6 1
ch 0 d 20 4 3 4 6 7
pg 2 0 3 4 e i 1 0
pg 2 0 6 7 e i 2 3
ch 0 d 4 2 0 4
pg 2 0 0 4 e i 0 1
qry
prd ge 0 4
prd eq 0 3
prj 0
end
""")

_add("prj-chunk-sum-whole", """
seg 10 6 2
ch 0 p 21
pg 3 0 1 3 e v 1 2 3
pg 3 0 4 6 e v 4 5 6
ch 1 p 60
pg 6 0 5 15 e v 5 7 9 11 13 15
qry
prd ge 1 5
prj 0
end
""")

_add("prj-chunk-sum-blocked", """
seg 10 9 2
ch 0 p 45
pg 3 0 1 3 e v 1 2 3
pg 3 0 4 6 e v 4 5 6
pg 3 0 7 9 e v 7 8 9
ch 1 p 78
pg 3 0 10 12 e v 10 11 12
pg 3 0 0 2 e v 0 1 2
pg 3 0 13 15 e v 13 14 15
qry
prd ge 1 10
prj 0
end
""")

_add("prj-chunk-sum-pinned-dead", """
seg 10 9 2
ch 0 p 40
pg 3 0 1 3 e v 1 2 3
pg 3 1 5 5 e v 5 - 5
pg 3 0 7 9 e v 7 8 9
ch 1 p 78
pg 3 0 10 12 e v 10 11 12
pg 3 0 0 2 e v 0 1 2
pg 3 0 13 15 e v 13 14 15
qry
prd ge 1 10
prj 0
end
""")

_add("prj-chunk-sum-together", """
seg 5 4 1
ch 0 p 73
pg 2 0 12 16 e v 16 12
pg 2 0 19 26 e v 26 19
qry
prd ge 0 11
prj 0
end
""")

_add("prj-pinned-nulls-sum", """
seg 10 4 1
ch 0 d 36 3 11 12 13
pg 2 1 11 11 e i 0 -
pg 2 0 12 13 e v 13 12
qry
prd ge 0 12
prj 0
end
""")

_add("prj-reads-in-page-order", """
seg 10 7 2
ch 0 p 95
pg 2 0 12 15 e v 12 15
pg 3 0 13 15 e v 13 13 15
pg 2 0 13 14 e v 14 13
ch 1 p 17
pg 3 0 1 11 e v 5 1 11
ch 1 p 0
pg 1 1 - - e v -
pg 3 3 - - e v - - -
qry
prd nn 1
prj 0
end
""")

_add("prj-chunk-sum-update", """
seg 5 9 1
ch 0 p 58
pg 3 0 10 12 e v 10 11 12
pg 2 0 12 13 e v 12 13
ch 0 p 42
pg 2 0 10 11 e v 10 11
pg 2 0 10 11 e v 10 11
up 0 7 10
qry
prd ge 0 10
prj 0
end
""")

_add("dec-hits-over-page", """
seg 5 5 2
ch 0 p 36
pg 2 1 10 10 w v - 10
pg 3 0 1 17 e v 17 8 1
ch 1 p 9
pg 3 0 1 3 e v 1 2 3
pg 2 1 3 3 e v - 3
qry
prd ge 1 1
prj 0
end
qry
prd nn 0
prd ne 1 1
prj 0
end
""")

_add("mem-counts-exact-from-start", """
seg 10 9 1
ch 0 p 23
pg 2 0 2 9 e v 2 9
pg 2 0 4 8 e v 4 8
ch 0 p 21
pg 3 2 3 3 e v - 3 -
pg 2 0 9 9 e v 9 9
qry
prd eq 0 9
prj 0
end
qry
prd le 0 9
prd ne 0 4
prj 0
end
""")

_add("ord-read-counts-exact", """
seg 5 6 3
ch 0 p 292
pg 2 0 45 52 e v 52 45
pg 2 0 45 50 w v 44 50
pg 2 0 44 57 e v 44 57
ch 1 p 172
pg 4 0 41 45 e v 43 43 45 41
ch 1 p 0
pg 2 2 - - e v - -
ch 2 p 3
pg 3 1 0 2 e v 0 - 2
pg 1 0 1 1 e v 1
ch 2 p 0
pg 2 2 - - e v - -
qry
prd ne 0 57
prj 1
end
qry
prd le 2 1
prd eq 0 52
prj 2
end
""")

_add("upd-count-over-page-as-written", """
seg 10 9 2
ch 0 p 56
pg 4 0 10 17 e v 17 14 10 15
ch 0 p 56
pg 2 0 13 15 e v 13 15
pg 3 1 11 17 e v 17 - 11
ch 1 p 0
pg 1 1 - - e v -
pg 1 1 - - e v -
pg 2 2 - - e v - -
pg 2 2 - - e v - -
ch 1 p 13
pg 1 0 2 2 e v 2
pg 2 0 5 6 e v 5 6
up 0 6 -
qry
prd nu 0
prj 1
end
qry
prd ne 0 15
prj 0
end
""")

_add("upd-read-not-merged", """
seg 10 7 1
ch 0 p 263
pg 2 0 42 44 e v 44 42
pg 2 0 42 46 e v 42 46
pg 2 1 45 45 e v - 45
pg 1 0 44 44 e v 44
up 0 3 42
qry
prd le 0 44
prj 0
end
""")

_add("ord-read-raises-repush", """
seg 10 14 2
ch 0 p 638
pg 3 0 28 110 e v 28 110 56
pg 5 0 35 53 e v 36 36 35 52 53
pg 6 0 35 46 e v 35 37 42 46 37 35
ch 1 p 62
pg 3 0 13 32 e v 17 13 32
ch 1 p 19
pg 1 0 19 19 e v 19
ch 1 p 42
pg 4 0 4 20 e v 12 6 4 20
ch 1 p 9
pg 1 0 9 9 e v 9
ch 1 p 79
pg 4 0 11 26 e v 26 11 19 23
ch 1 p 37
pg 1 0 37 37 e v 37
qry
prd ge 0 35
prd ge 0 53
prd le 1 13
prj 1
end
""")

_add("ord-read-raises-stale", """
seg 10 12 2
ch 0 p 989
pg 3 0 38 45 e v 45 45 38
pg 6 0 74 145 e v 129 116 145 74 132 92
pg 3 0 44 65 e v 65 64 44
ch 1 p 29
pg 1 0 29 29 e v 29
ch 1 p 65
pg 4 0 0 35 e v 4 26 35 0
ch 1 p 23
pg 2 0 8 15 e v 15 8
ch 1 p 75
pg 2 0 36 39 e v 39 36
ch 1 p 69
pg 3 0 18 32 e v 32 18 19
qry
prd ne 0 116
prd ge 0 44
prd ge 0 45
prj 1
end
""")

_add("prj-consult-needs-live-row", """
seg 10 6 2
ch 0 d 42 1 10
pg 3 0 10 10 w i 0 0 0
pg 3 0 3 5 e v 3 4 5
ch 1 p 24
pg 3 0 0 0 e v 0 0 0
pg 3 0 7 9 e v 7 8 9
qry
prd ge 1 5
prj 0
end
""")

_add("prj-consult-spares-read", """
seg 10 9 2
ch 0 d 72 1 10
pg 3 0 10 10 w i 0 0 0
pg 3 0 10 10 w i 0 0 0
pg 3 0 3 5 e v 3 4 5
ch 1 p 42
pg 3 0 0 0 e v 0 0 0
pg 3 0 1 9 e v 1 8 9
pg 3 0 7 9 e v 7 8 9
qry
prd ge 1 5
prj 0
end
""")

_add("prj-consult-not-sparing", """
seg 10 6 2
ch 0 d 40 1 10
pg 3 1 10 10 w i 0 - 0
pg 3 1 10 10 w i 0 0 -
ch 1 p 42
pg 3 0 1 9 e v 1 8 9
pg 3 0 7 9 e v 7 8 9
qry
prd ge 1 5
prj 0
end
""")

_add("flt-consult-settles-whole-chunk", """
seg 5 5 2
ch 0 d 106 3 17 22 25
pg 2 0 17 22 e i 1 0
pg 2 0 20 25 w i 0 2
pg 1 0 25 25 w i 2
ch 1 p 22
pg 3 0 1 18 e v 3 18 1
ch 1 p 28
pg 2 0 10 18 e v 18 10
qry
prd ne 0 20
prd ge 1 12
prd eq 0 24
prj 0
end
""")

ORDER = sorted(CASES)


def prog(name):
    return CASES[name]
