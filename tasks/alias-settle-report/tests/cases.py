"""The enumerated report sets, one per rule the verifier grades.

Each name says which reading the set exists to fail, and each fence that says
"this must still work" ships beside the case that says "this must not". The set
is fixed, it is in the bundle, and its expected rows are in gt.json. It is not
what the submission is really graded on - see gen.py - but a failure here names
the rule that broke, where a failure among three hundred generated sets says
only that something did.

The three sets that ship in the tree under /app/sets are included verbatim, so a
submission that only ever ran those is graded on them too.
"""

SETS = {}


def _add(name, text):
    SETS[name] = text.strip() + "\n"


_add("rep-is-least", """
watch 5
run r0 5
tag m0 2 5
go
tie m0 5 2
shut m0
post r0 5 40
shut r0
""")

_add("auth-run-then-key", """
watch 3
run r0 9
run r1 3
tag m0 3 9
go
post r1 3 77
post r0 9 41
tie m0 3 9
shut r0
shut r1
shut m0
""")

_add("auth-inside-run", """
watch 8
run r0 3 8
tag m0 3 8
go
post r0 8 20
tie m0 3 8
shut m0
post r0 3 55
shut r0
""")

_add("weld-takes-score", """
watch 6
run r0 1
run r1 6
tag m0 1 6
go
post r1 6 88
post r0 1 12
tie m0 1 6
shut m0
shut r0
shut r1
""")

_add("reach-holds-earlier", """
watch 2
run r0 9
run r1 2
tag m0 2 9
go
post r1 2 50
post r0 9 33
shut r0
shut r1
shut m0
""")

_add("two-file-one-tick", """
watch 7 2
run r0 2 7
tag m0 1 2 7
go
post r0 7 10
post r0 2 20
shut r0
shut m0
""")

_add("two-watch-one-cell", """
watch 2 5
run r0 2 5
tag m0 2 5
go
post r0 5 40
tie m0 2 5
shut m0
post r0 2 70
shut r0
""")

_add("wait-for-tag", """
watch 7
run r0 7
tag m0 7 1
go
post r0 7 10
shut m0
shut r0
""")

_add("two-hop-reach", """
watch 5
run r0 5
tag m0 5 6
tag m1 6 2
go
post r0 5 70
shut r0
tie m1 6 2
tie m0 5 6
shut m0
shut m1
""")

_add("three-hop-reach", """
watch 6
run r0 6
tag m0 6 7
tag m1 7 8
tag m2 8 1
go
post r0 6 20
shut r0
shut m0
shut m1
shut m2
""")

_add("shut-tag-inert", """
watch 5
run r0 5
tag m0 1 5
go
shut m0
post r0 5 30
shut r0
""")

_add("tag-inside-cell", """
watch 5
run r0 5
tag m0 5 8
tag m1 5 8
go
tie m0 5 8
post r0 5 30
shut m0
shut m1
shut r0
""")

_add("higher-keys-harmless", """
watch 2
run r0 2
tag m0 2 9
go
post r0 2 44
shut r0
shut m0
""")

_add("bar-blocks-hop", """
watch 4
run r0 4
tag m0 1 4
go
bar m0 1 4
post r0 4 50
shut r0
shut m0
""")

_add("bar-blocks-chain", """
watch 5
run r0 5
tag m0 5 6
tag m1 6 1
go
bar m1 1 6
post r0 5 90
shut r0
tie m0 5 6
shut m0
shut m1
""")

_add("bar-off-the-step", """
watch 3
run r0 3
tag m0 3 8
tag m1 8 1
go
bar m1 1 3
post r0 3 60
shut r0
tie m0 3 8
shut m0
shut m1
""")

_add("bar-leaves-a-detour", """
watch 5
run r0 5
tag m0 5 6
tag m1 6 1
tag m2 5 7
tag m3 7 1
go
bar m1 1 6
post r0 5 90
shut r0
shut m0
shut m1
shut m2
shut m3
""")

_add("bar-arrives-late", """
watch 3
run r0 3
tag m0 1 3
go
post r0 3 60
shut r0
bar m0 1 3
shut m0
""")

_add("bar-after-weld", """
watch 4
run r0 4
tag m0 4 9
tag m1 9 1
go
bar m1 1 9
post r0 4 15
tie m0 4 9
shut r0
shut m0
shut m1
""")

_add("pending-beats", """
watch 6
run r0 6
run r1 6
tag m0 6 3
go
post r1 6 25
shut r1
shut m0
post r0 6 15
shut r0
""")

_add("pending-loses", """
watch 6
run r0 6
run r1 6
tag m0 6 9
go
post r0 6 15
shut r0
shut r1
shut m0
""")

_add("pending-in-reach", """
watch 4
run r0 9
run r1 4
tag m0 4 9
go
post r1 4 33
shut r1
shut m0
post r0 9 12
shut r0
""")

_add("pending-out-of-reach", """
watch 4
run r0 9
run r1 4
tag m0 4 9
go
bar m0 4 9
post r1 4 33
shut r1
shut m0
post r0 9 12
shut r0
""")

_add("no-post-yet", """
watch 2
run r0 2
tag m0 2 5
go
shut m0
post r0 2 9
shut r0
""")

_add("all-at-the-end", """
watch 1 4 7
run r0 1 4 7
tag m0 1 4 7 9
go
post r0 7 11
post r0 4 22
post r0 1 33
shut r0
shut m0
""")

_add("weld-then-reach", """
watch 8
run r0 8
tag m0 8 5
tag m1 5 2
go
post r0 8 70
tie m0 8 5
shut r0
bar m1 2 5
shut m0
shut m1
""")

# The three sets that ship under /app/sets, as literals. They are NOT read off
# disk: the verifier image moves the pristine tree out of /tests at build time,
# so a path into tests/pristine resolves on the authoring host and raises inside
# the container. authoring/sync.py holds these against the tree on every run so
# the two copies cannot drift.

_add("plain", """
watch 2
run r0 9
run r1 2
tag m0 2 9
go
post r1 2 40
post r0 9 17
tie m0 2 9
shut m0
shut r0
shut r1
""")

_add("chain", """
watch 5
run r0 5
tag m0 5 6
tag m1 6 2
go
post r0 5 70
shut r0
tie m1 6 2
tie m0 5 6
shut m0
shut m1
""")

_add("barred", """
watch 5
run r0 5
tag m0 5 6
tag m1 6 2
go
post r0 5 70
bar m1 2 5
shut r0
tie m1 6 2
shut m0
shut m1
""")

_add("gone-holds-nothing", """
watch 2 7
run r0 2
run r1 7
tag m0 2 7
go
post r0 2 40
post r1 7 50
shut r0
shut r1
shut m0
""")

_add("one-going-frees-the-next", """
watch 3 8
run r0 3
run r1 8
tag m0 3 8
go
post r1 8 50
post r0 3 20
shut m0
shut r0
shut r1
""")

_add("neither-frees-the-other", """
watch 3 8
run r0 8
run r1 3
tag m0 3 8
go
post r1 3 40
post r0 8 50
shut m0
shut r0
shut r1
""")

_add("gone-frees-a-run-too", """
watch 2 9
run r0 2 9
run r1 9
tag m0 2 9
go
post r0 9 30
post r0 2 15
shut r0
shut m0
shut r1
""")
