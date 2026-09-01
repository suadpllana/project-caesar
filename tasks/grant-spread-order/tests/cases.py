"""The enumerated journals: one per rule, each named for the reading it exists to fail.

The run may read this file. These are thirty small histories with an obvious purpose
and they are not where a wrong submission is caught - the three hundred generated ones
are. What these buy is a legible failure: when a submission is wrong, the name of the case
that failed says which rule it was wrong about, in one line, instead of "history g0173
diverged at operation 41".

Every fence in the set - the must-still-work side of a rule - is marked in its name with
"holds". A submission that overshoots into being conservative fails those exactly as hard
as a careless one fails the others.
"""

JRN = {}


def case(name, text):
    JRN[name] = text.strip() + "\n"


# ------------------------------------------------------------------ the ordering keys

case("reach-beats-tree", """
nd r -
nd a r
mb g1 u1 +
st r u1 0 a b
st a g1 0 d b
ak u1 a 0
""")

case("reach-beats-tree-deep", """
nd r -
nd a r
nd b a
nd c b
mb g1 u1 +
mb g2 g1 +
st r g1 0 d b
st c g2 0 a b
ak u1 c 0
""")

case("placed-here-beats-arrived", """
nd r -
nd a r
st r u1 0 a b
st a u1 0 d b
ak u1 a 0
""")

case("later-act-wins", """
nd r -
nd a r
nd b a
st r u1 0 d b
st a u1 0 a b
ak u1 b 0
""")

case("later-act-wins-reversed", """
nd r -
nd a r
nd b a
st r u1 0 a b
st a u1 0 d b
ak u1 b 0
""")

case("no-deny-wins-rule", """
nd r -
nd a r
nd b a
st a u1 0 d b
st r u1 0 a b
ak u1 b 0
""")

case("hops-two-loses-to-one", """
nd r -
nd a r
mb g1 u1 +
mb g2 g1 +
st a g2 0 a b
st a g1 0 d b
ak u1 a 0
""")

case("unreachable-subject-ignored", """
nd r -
nd a r
mb g1 u2 +
st a g1 0 a b
st a u1 0 d b
ak u1 a 0
""")

case("nothing-matching-refuses", """
nd r -
nd a r
st a u2 0 a b
ak u1 a 0
""")

case("membership-read-at-decision", """
nd r -
nd a r
st a g1 0 a b
ak u1 a 0
mb g1 u1 +
ak u1 a 0
mb g1 u1 -
ak u1 a 0
""")

# ------------------------------------------------------------------ scope

case("down-only-skips-its-node", """
nd r -
nd a r
st r u1 0 a d
ak u1 r 0
ak u1 a 0
""")

case("down-only-reaches-every-depth", """
nd r -
nd a r
nd b a
nd c b
st r u1 0 a d
ak u1 c 0
""")

case("here-only-stays-put", """
nd r -
nd a r
st r u1 0 a h
ak u1 r 0
ak u1 a 0
""")

case("here-only-replacing-withdraws", """
nd r -
nd a r
nd b a
st r u1 0 a b
ak u1 b 0
st r u1 0 a h
ak u1 b 0
ak u1 r 0
""")

case("scope-rewritten-not-carried", """
nd r -
nd a r
nd b a
st r u1 0 a d
ak u1 a 0
ak u1 b 0
""")

case("both-scope-holds", """
nd r -
nd a r
st r u1 0 a b
ak u1 r 0
ak u1 a 0
""")

# ------------------------------------------------------------------ the bar

case("bar-stops-what-arrives", """
nd r -
nd a r
sl a
st r u1 0 a b
ak u1 a 0
""")

case("bar-stops-the-subtree", """
nd r -
nd a r
nd b a
sl a
st r u1 0 a b
ak u1 b 0
""")

case("bar-keeps-what-it-had-holds", """
nd r -
nd a r
st r u1 0 a b
sl a
ak u1 a 0
""")

case("bar-does-not-stop-a-clear-below-it", """
nd r -
nd a r
nd b a
st r u1 0 a b
sl b
cl r u1 0
ak u1 a 0
ak u1 b 0
""")

case("planting-on-a-barred-node-holds", """
nd r -
nd a r
nd b a
sl a
st a u1 0 a b
ak u1 a 0
ak u1 b 0
""")

case("resume-takes-the-chain", """
nd r -
nd a r
nd b a
sl a
st r u1 0 a b
ak u1 b 0
us a
ak u1 a 0
ak u1 b 0
""")

# ------------------------------------------------------------------ structure

case("move-reflows-the-subtree", """
nd r -
nd x r
nd y r
nd a x
nd b a
st x u1 0 a b
st y u1 0 d b
mv a y
ak u1 a 0
ak u1 b 0
""")

case("move-drops-what-is-no-longer-above", """
nd r -
nd x r
nd y r
nd a x
st x u1 0 a b
mv a y
ak u1 a 0
""")

case("move-keeps-what-is-still-above-holds", """
nd r -
nd x r
nd a x
nd b x
nd c a
st x u1 0 a b
mv c b
ak u1 c 0
""")

case("barred-node-carries-its-snapshot", """
nd r -
nd x r
nd y r
nd a x
st x u1 0 a b
sl a
mv a y
ak u1 a 0
""")

case("barred-node-stops-the-reflow", """
nd r -
nd x r
nd y r
nd a x
nd b a
st x u1 0 a b
sl a
mv a y
ak u1 b 0
""")

case("direct-placement-survives-a-move-holds", """
nd r -
nd x r
nd y r
nd a x
st a u1 0 a b
st y u1 0 d b
mv a y
ak u1 a 0
""")

case("a-new-node-takes-the-offer", """
nd r -
st r u1 0 a b
nd a r
ak u1 a 0
""")

case("an-entry-never-returns-to-its-origin", """
nd r -
nd x r
nd a x
nd b a
st a u1 0 a b
sl b
mv b r
mv a b
st a u1 0 d h
ak u1 a 0
""")

PROGS = JRN
