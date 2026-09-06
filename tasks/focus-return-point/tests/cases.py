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

case("comp-back-from-dropped-place", """
screen m
w w1 m foc
w c m comp
w w2 c foc
w w3 c foc
w w4 m foc
push m
tab
next
prev
drop w2
back
tab
drop w3
back
""")

# Nested-scope extension

case('nested-arrows-climb-without-screen-wrap', 'screen s\nw a s foc\nw c s comp\nw x c foc\nw d c comp\nw i d foc\nw j d foc\nw y c foc\nw z s foc\npush s\ntab\nnext\nnext\nnext\nprev\nprev\nprev\nprev\ntab\nback\nwant j\ntab\nback\n')

case('nested-memory-remembers-branch-not-leaf', 'screen s\nw a s foc\nw c s comp\nw x c foc\nw d c comp\nw i d foc\nw j d foc\nw y c foc\nw z s foc\npush s\nwant j\ntab\nhide j\nback\nshow j\ntab\nback\n')

case('nested-return-updates-every-ancestor', 'screen s\nw a s foc\nw c s comp\nw x c foc\nw d c comp\nw i d foc\nw j d foc\nw y c foc\nw z s foc\nscreen modal\nw m modal foc\npush s\nwant j\npush modal\nwant i\npop modal\ntab\nback\n')

case('nested-dropped-slot-leaves-outermost', 'screen s\nw a s foc\nw c s comp\nw x c foc\nw d c comp\nw i d foc\nw j d foc\nw y c foc\nw z s foc\npush s\nwant j\ndrop j\nback\ntab\nwant i\ndrop i\ntab\nback\n')

case('nested-moved-branch-invalidates-scope', 'screen s\nw a s foc\nw c s comp\nw x c foc\nw d c comp\nw i d foc\nw j d foc\nw y c foc\nw z s foc\npush s\nwant j\ntab\nmove d s 2\nback\nback\nnext\n')

case('nested-memory-of-unselected-group-member', 'screen s\nw a s foc\nw c s comp\nw x c foc grp=g\nw y c foc grp=g\nw d c comp\nw i d foc grp=g sel\nw j d foc grp=g\nw z s foc\npush s\ntab\nnext\nwant j\ntab\npick y\nback\nprev\nnext\n')

case('nested-fallback-applies-local-group', 'screen s\nw a s foc\nw c s comp\nw x c foc\nw d c comp\nw i d foc grp=g\nw j d foc grp=g sel\nw y c foc\nw z s foc\npush s\nwant i\ntab\nhide i\nback\nnext\nprev\n')

case('nested-empty-branch-falls-to-parent-first', 'screen s\nw a s foc\nw c s comp\nw x c foc\nw d c comp\nw i d foc\nw j d foc\nw y c foc\nw z s foc\npush s\nwant j\ntab\nhide d\nback\nshow d\nnext\n')

case('nested-hidden-return-and-out-of-order-pop', 'screen s\nw a s foc\nw c s comp\nw x c foc\nw d c comp\nw i d foc\nw j d foc\nw y c foc\nw z s foc\nscreen m\nw m1 m foc\nscreen n\nw n1 n foc\npush s\nwant j\npush m\npush n\nhide d\npop m\npop n\nback\nshow d\ntab\nnext\n')

case('nested-drop-container-then-move-surviving-parent', 'screen s\nw a s foc\nw c s comp\nw x c foc\nw d c comp\nw i d foc\nw j d foc\nw y c foc\nw z s foc\npush s\nwant j\ndrop d\nmove c s 2\nback\ntab\n')


# Rebuilt controls reuse names, never lifetimes. Inputs only.
CASES.update({
    'instance-return-same-slot': 'screen s\nw a s foc\nw x s foc\nw b s foc\nscreen m\nw q m foc\npush s\nwant x\npush m\ndrop x\nadd x s 1 foc\npop m\ntab\n',
    'instance-return-different-slot': 'screen s\nw a s foc\nw x s foc\nw b s foc\nscreen m\nw q m foc\npush s\nwant x\npush m\ndrop x\nadd x s 2 foc\npop m\ntab\n',
    'instance-lost-does-not-follow-replacement': 'screen s\nw a s foc\nw x s foc\nw b s foc\npush s\nwant x\ndrop x\nadd x s 2 foc\ntab\nwant x\n',
    'instance-held-before-push': 'screen s\nw a s foc\nw x s foc\nw b s foc\nwant x\ndrop x\nadd x s 2 foc auto\npush s\ntab\n',
    'instance-new-want-replaces-old-want': 'screen s\nw a s foc\nw x s foc\nw b s foc\nwant x\ndrop x\nadd x s 2 foc\nwant x\npush s\n',
    'instance-leaf-memory': 'screen s\nw c s comp\nw a c foc\nw x c foc\nw z s foc\npush s\nwant x\ntab\ndrop x\nadd x c 1 foc\nback\n',
    'instance-composite-memory': 'screen s\nw c s comp\nw a c foc\nw x c foc\nw z s foc\npush s\nwant x\ntab\ndrop c\nadd c s 0 comp\nadd a c 0 foc\nadd x c 1 foc\nback\n',
    'instance-parent-slot': 'screen s\nw a s foc\nw box s\nw x box foc\nw b s foc\nscreen m\nw q m foc\npush s\nwant x\npush m\ndrop box\nadd box s 0\nadd x box 0 foc\npop m\ntab\n',
    'instance-cross-screen-reuse': 'screen s\nw a s foc\nw x s foc\nw b s foc\nscreen m\nw q m foc\npush s\nwant x\npush m\nwant x\ndrop x\nadd x m 0 foc\nwant x\npop m\ntab\n',
    'instance-two-retired-generations': 'screen s\nw a s foc\nw x s foc\nw b s foc\nscreen m\nw q m foc\npush s\nwant x\npush m\ndrop x\nadd x s 0 foc\ndrop x\nadd x s 2 foc\npop m\nback\n',
    'instance-return-through-popped-screen': 'screen s\nw a s foc\nw x s foc\nw b s foc\nscreen m\nw q m foc\nscreen n\nw r n foc\npush s\nwant x\npush m\npush n\npop m\ndrop x\nadd x s 2 foc\npop n\ntab\n',
    'instance-old-branch-is-not-new-branch': 'screen s\nw c s comp\nw a c foc\nw d c comp\nw x d foc\nw y d foc\nw z s foc\npush s\nwant y\ntab\ndrop d\nadd d c 1 comp\nadd x d 0 foc\nadd y d 1 foc\nback\nnext\n',
})


# Nested render commits and aborts. Inputs only.
CASES.update({
    'tx-abandoned-tombstone-does-not-follow-moved-widget': 'screen s\nw a s foc\nw box s\nw b box foc\nw c box foc\nw h s\nw e h foc\nw z s foc\npush s\nwant b\nbegin\ndrop b\nabort\nmove b h 1\ndrop h\ntab\n',
    'tx-transient-hide-show': 'screen s\nw a s foc\nw b s foc\nw c s foc\npush s\nwant b\nbegin\nhide b\nshow b\ncommit\ntab\n',
    'tx-committed-hide': 'screen s\nw a s foc\nw b s foc\nw c s foc\npush s\nwant b\nbegin\nhide b\ncommit\ntab\nback\n',
    'tx-keys-use-final-order': 'screen s\nw a s foc\nw b s foc\nw c s foc\nw d s foc\npush s\nbegin\ntab\nmove b s 3\ntab\ncommit\nback\n',
    'tx-want-then-back-final-order': 'screen s\nw a s foc\nw b s foc\nw c s foc\nw d s foc\npush s\nbegin\nwant c\nmove c s 0\nback\ncommit\ntab\n',
    'tx-early-want-retired-instance': 'screen s\nw a s foc\nw x s foc\nw c s foc\npush s\nwant c\nbegin\nwant x\ndrop x\nadd x s 0 foc\ncommit\n',
    'tx-later-want-replacement-instance': 'screen s\nw a s foc\nw x s foc\nw c s foc\npush s\nwant c\nbegin\nwant x\ndrop x\nadd x s 0 foc\nwant x\ncommit\n',
    'tx-abort-keeps-earlier-offscreen-request': 'screen s\nw a s foc\nscreen m\nw x m foc\nw y m foc\nwant y\npush s\nbegin\nwant x\nabort\npush m\npop m\n',
    'tx-inner-commit-outer-abort': 'screen s\nw a s foc\nw b s foc\nw c s foc\npush s\nwant b\nbegin\ndrop b\nbegin\nadd b s 0 foc\nwant b\ncommit\nabort\ntab\n',
    'tx-inner-abort-outer-commit': 'screen s\nw a s foc\nw b s foc\nw c s foc\npush s\nwant b\nbegin\nhide b\nbegin\nshow b\ndrop a\nwant c\nabort\ncommit\ntab\n',
    'tx-nested-queue-merge-order': 'screen s\nw a s foc\nw b s foc\nw c s foc\nw d s foc\npush s\nbegin\ntab\nbegin\ntab\ncommit\nback\ncommit\ntab\n',
    'tx-nested-queue-abort-order': 'screen s\nw a s foc\nw b s foc\nw c s foc\nw d s foc\npush s\nbegin\ntab\nbegin\ntab\nabort\ntab\ncommit\nback\n',
    'tx-final-group-selection-before-navigation': 'screen s\nw a s foc\nw c s comp\nw u c foc grp=g sel\nw v c foc grp=g\nw w c foc\nw z s foc\npush s\nbegin\ntab\npick v\nnext\ncommit\nback\n',
    'tx-abort-restores-remembered-branch-instances': 'screen s\nw a s foc\nw c s comp\nw u c foc\nw v c foc\nw z s foc\npush s\ntab\nnext\ntab\nbegin\ndrop c\nadd c s 1 comp\nadd v c 0 foc\ntab\nabort\nback\n',
    'tx-commit-checks-memory-in-final-scope': 'screen s\nw a s foc\nw c s comp\nw u c foc\nw d c comp\nw i d foc\nw j d foc\nw v c foc\nw z s foc\npush s\ntab\nnext\nnext\ntab\nbegin\nmove d s 1\nback\ncommit\nnext\n',
    'tx-fixed-slot-survives-transient-siblings': 'screen s\nw a s foc\nw b s foc\nw c s foc\nw d s foc\npush s\nwant b\nbegin\ndrop b\nadd x s 1 foc\ndrop x\nadd y s 0 foc\ncommit\ntab\n',
    'tx-inner-abort-discards-old-drop-position': 'screen s\nw a s foc\nw b s foc\nw c s foc\npush s\nwant b\nbegin\nbegin\nmove b s 0\ndrop b\nabort\ndrop b\nadd x s 1 foc\ncommit\ntab\n',
    'tx-abort-restores-id-lookup-and-old-slot': 'screen s\nw a s foc\nw b s foc\nw c s foc\npush s\nwant b\nbegin\ndrop b\nadd b s 0 foc\nabort\ndrop b\nadd b s 0 foc\ntab\n',
    'tx-missing-want-does-not-bind-future-add': 'screen s\nw a s foc\nw b s foc\npush s\nbegin\nwant x\nadd x s 0 foc\ncommit\nback\n',
    'tx-kept-request-retains-dropped-instance': 'screen s\nw a s foc\nscreen m\nw p m foc\nw x m foc\nw q m foc\npush s\nbegin\nwant x\ndrop x\nadd x m 0 foc\ncommit\npush m\ntab\npop m\n',
    'tx-only-retained-offscreen-wants-compete': 'screen s\nw a s foc\nscreen m\nw x m foc\nw y m foc\nw z m foc\npush s\nbegin\nwant x\nbegin\nwant y\nabort\nwant z\ncommit\npush m\n',
})
