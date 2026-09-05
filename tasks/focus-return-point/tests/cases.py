"""The enumerated scripts, one per rule, named for the reading each exists to fail.

Every one of these has an expected trail that was derived by hand from the brief before
either implementation produced it (authoring/handcheck.py holds those literals), which is
the only defence against both implementations sharing one author's misreading.
"""

CASES = {}


def case(name, text):
    CASES[name] = text.strip("\n") + "\n"


# ------------------------------------------------------------------ reach

case("reach-inherits-hidden", """
screen m
w b m
w w1 b foc
w w2 m foc
w w3 m foc
push m
hide b
tab
tab
show b
tab
""")

case("reach-inherits-shut", """
screen m
w b m
w w1 b foc
w w2 b foc
w w3 m foc
push m
tab
shut b
tab
open b
back
""")

case("reach-inherits-disabled-focused", """
screen m
w b m
w w1 b foc
w w2 m foc
push m
off b
tab
on b
tab
""")

# ------------------------------------------------------------------ groups

case("group-selected-is-the-stop", """
screen m
w w1 m foc
w w2 m foc grp=g
w w3 m foc grp=g sel
w w4 m foc grp=g
w w5 m foc
push m
tab
tab
pick w4
back
back
""")

case("group-none-selected", """
screen m
w w1 m foc
w w2 m foc grp=g
w w3 m foc grp=g
w w4 m foc
push m
tab
tab
pick w3
back
""")

case("group-selected-unreachable", """
screen m
w w1 m foc
w w2 m foc grp=g
w w3 m foc grp=g sel hid
w w4 m foc
push m
tab
tab
show w3
back
""")

case("group-unselected-holds-focus", """
screen m
w w1 m foc
w w2 m foc grp=g sel
w w3 m foc grp=g
w w4 m foc
push m
want w3
tab
want w3
back
""")

# --------------------------------------------------------------- composites

case("comp-is-one-stop", """
screen m
w w1 m foc
w c m comp
w w2 c foc
w w3 c foc
w w4 c foc
w w5 m foc
push m
tab
next
next
tab
back
""")

case("comp-back-lands-on-memory", """
screen m
w w1 m foc
w c m comp
w w2 c foc
w w3 c foc
w w4 c foc
w w5 m foc
push m
tab
next
tab
back
back
tab
""")

case("comp-memory-from-request", """
screen m
w w1 m foc
w c m comp
w w2 c foc
w w3 c foc
w w4 c foc
w w5 m foc
push m
want w4
tab
back
tab
tab
""")

case("comp-memory-gone", """
screen m
w w1 m foc
w c m comp
w w2 c foc
w w3 c foc
w w4 c foc
w w5 m foc
push m
tab
next
next
tab
drop w4
back
tab
hide w2
back
""")

case("comp-arrows-do-not-wrap", """
screen m
w c m comp
w w1 c foc
w w2 c foc
w w3 c foc
w w4 m foc
push m
prev
next
next
next
prev
prev
prev
""")

case("comp-empty-is-no-stop", """
screen m
w w1 m foc
w c m comp
w w2 c foc
w w3 m foc
push m
hide w2
tab
tab
show w2
tab
""")

# ---------------------------------------------------------------- screens

case("push-lands-on-auto", """
screen m
w w1 m foc
w w2 m foc
screen d
w d1 d foc
w d2 d foc auto hid
w d3 d foc auto
w d4 d foc
push m
push d
tab
pop d
""")

case("push-without-auto", """
screen m
w w1 m foc
screen d
w b d
w d1 b foc
w d2 d foc
push m
push d
""")

case("push-nothing-to-take", """
screen m
w w1 m foc
screen d
w d1 d foc hid
w d2 d foc off
push m
push d
tab
show d1
tab
""")

case("pop-restores-the-widget", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
tab
push d
tab
pop d
tab
""")

case("pop-restores-lazily", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
tab
push d
off w2
on w2
pop d
tab
""")

case("pop-target-still-unreachable", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
tab
push d
hide w2
pop d
tab
back
back
""")

case("pop-target-dropped", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
tab
push d
drop w2
pop d
tab
""")

case("pop-out-of-order", """
screen a
w a1 a foc
w a2 a foc
w a3 a foc
screen b
w b1 b foc
w b2 b foc
screen c
w c1 c foc
push a
tab
push b
tab
push c
pop b
pop c
tab
""")

case("pop-out-of-order-target-gone", """
screen a
w a1 a foc
w a2 a foc
w a3 a foc
screen b
w b1 b foc
w b2 b foc
screen c
w c1 c foc
push a
tab
push b
tab
push c
drop a2
pop b
pop c
tab
""")

case("pop-out-of-order-twice", """
screen a
w a1 a foc
w a2 a foc
screen b
w b1 b foc
screen c
w c1 c foc
w c2 c foc
screen d
w d1 d foc
push a
tab
push b
push c
tab
push d
pop b
pop c
pop d
""")

case("pop-the-last-screen", """
screen m
w w1 m foc
w w2 m foc
screen d
w d1 d foc
push m
tab
pop m
tab
push d
back
pop d
tab
""")

# --------------------------------------------------------------- requests

case("want-held-for-a-screen-below", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
push d
want w3
tab
pop d
""")

case("want-held-beats-the-return", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
tab
push d
want w3
pop d
""")

case("want-held-latest-wins", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
push d
want w3
want w2
pop d
""")

case("want-held-unreachable-at-return", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
push d
want w2
off w2
pop d
tab
""")

case("want-held-re-enabled-before-return", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
push d
want w2
off w2
on w2
pop d
""")

case("want-held-before-the-push", """
screen m
w w1 m foc
screen d
w d1 d foc
w d2 d foc auto
w d3 d foc
push m
want d3
push d
""")

case("want-unreachable-is-ignored", """
screen m
w w1 m foc
w w2 m foc hid
w w3 m foc
push m
want w2
tab
want w2
tab
""")

case("want-inside-composite", """
screen m
w w1 m foc
w c m comp
w w2 c foc
w w3 c foc
push m
want w3
next
back
tab
""")

# ------------------------------------------------------------- focus lost

case("lost-starts-after-the-widget", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
w w4 m foc
push m
tab
tab
hide w3
tab
back
back
hide w1
back
""")

case("lost-widget-shown-again", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
push m
tab
hide w2
show w2
tab
back
back
""")

case("lost-container-dropped", """
screen m
w w1 m foc
w b m
w w2 b foc
w w3 b foc
w w4 m foc
push m
tab
tab
drop b
tab
""")

case("lost-container-dropped-then-parent", """
screen m
w w1 m foc
w o m
w b o
w w2 b foc
w w3 o foc
w w4 m foc
push m
tab
drop b
drop o
tab
""")

case("lost-insert-at-the-point", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
push m
tab
drop w2
add w5 m 1 foc
tab
""")

case("lost-point-does-not-move", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
w w4 m foc
push m
tab
drop w2
drop w1
tab
""")

case("lost-point-at-the-end", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
push m
back
drop w3
tab
back
""")

case("lost-moved-under-hidden", """
screen m
w w1 m foc
w b m hid
w w2 m foc
w w3 m foc
push m
tab
move w2 b 0
tab
show b
back
""")

case("lost-inside-composite", """
screen m
w w1 m foc
w c m comp
w w2 c foc
w w3 c foc
w w4 m foc
push m
tab
hide w2
tab
back
""")

case("pick-keeps-focus", """
screen m
w w1 m foc grp=g sel
w w2 m foc grp=g
w w3 m foc
push m
pick w2
tab
tab
""")

# ------------------------------------------------- rules the self-probe found undecided

case("comp-keys-leave-it", """
screen m
w w1 m foc
w c m comp
w w2 c foc
w w3 c foc
w w4 m foc
push m
tab
next
back
tab
hide w3
back
tab
drop w2
tab
""")

case("push-over-nothing", """
screen m
w w1 m foc
w w2 m foc
w w3 m foc
screen d
w d1 d foc
push m
tab
hide w2
push d
pop d
tab
show w2
back
""")

case("pop-out-of-order-with-held", """
screen a
w a1 a foc
w a2 a foc
w a3 a foc
screen b
w b1 b foc
screen c
w c1 c foc
push a
push b
push c
want a3
hide a3
pop b
show a3
pop c
tab
""")
