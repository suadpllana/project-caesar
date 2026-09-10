"""The enumerated programs: one per graded decision, plus the must-still-work side of each fence.

Each entry is named for the decision it separates. Their answers are frozen in gt.json,
which was written before the grading file and is checked against the sealed model on every
run, so a model that drifted cannot quietly redefine what correct means.
"""

CASES = {

# --- allocation --------------------------------------------------------------------

"alloc-best": """
dev 24
n a
w a/f 0 4
w a/g 0 6
w a/h 0 4
w a/i 0 6
x a/f
x a/h
f
w a/j 0 4
m a/j
f
""",

"alloc-fit": """
dev 24
n a
w a/f 0 6
w a/g 0 3
w a/h 0 4
w a/i 0 3
x a/f
x a/h
f
w a/j 0 4
m a/j
f
""",

"alloc-low": """
dev 24
n a
w a/f 0 4
w a/g 0 4
w a/h 0 4
w a/i 0 4
x a/f
x a/h
f
w a/j 0 4
m a/j
""",

"alloc-split": """
dev 16
n a
w a/f 0 4
w a/g 0 2
w a/h 0 4
w a/i 0 6
x a/g
x a/i
f
w a/j 0 8
m a/j
f
""",

"alloc-order": """
dev 20
n a
w a/f 0 3
w a/g 0 5
w a/h 0 3
w a/i 0 9
x a/f
x a/h
x a/i
f
w a/j 0 12
m a/j
f
""",

"alloc-none": """
dev 12
n a
w a/f 0 8
w a/g 0 5
f
w a/g 0 4
m a/g
f
""",

# --- rewrite in place --------------------------------------------------------------

"keep-sole": """
# a rewrite by the only claimant takes nothing from the free map
dev 32
n a
w a/f 0 8

w a/f 2 4
m a/f
f
w a/f 0 8   # and again over the whole item
f
""",

"keep-shared": """
dev 32
n a
n b
w a/f 0 8
s a/f 0 8 b/g 0
w a/f 2 4
m a/f
f
""",

"keep-mixed": """
dev 32
n a
n b
w a/f 0 12
s a/f 4 4 b/g 0
w a/f 0 12
m a/f
f
""",

"keep-self": """
dev 32
n a
w a/f 0 8
s a/f 0 4 a/f 4
m a/f
w a/f 0 4
m a/f
f
""",

"keep-tail": """
dev 32
n a
w a/f 0 6
w a/f 4 6
m a/f
f
""",

"keep-none": """
dev 32
n a
w a/f 0 6
t a/f 0
w a/f 0 6
m a/f
f
""",

# --- when a span goes back ---------------------------------------------------------

"span-hold": """
dev 32
n a
n b
w a/f 0 9
s a/f 0 9 b/g 0
w b/g 3 3
f
x b/g
f
c a
""",

"span-back": """
dev 32
n a
w a/f 0 5
w a/g 0 5
x a/f
f
x a/g
f
""",

"merge-runs": """
dev 24
n a
w a/f 0 6
w a/g 0 6
w a/h 0 6
x a/f
x a/h
f
x a/g
f
""",

"reuse-own": """
dev 16
n a
w a/f 0 6
w a/g 0 10
s a/f 0 3 a/f 3
f
w a/f 0 6
m a/f
f
""",

"room-after": """
dev 12
n a
n b
w a/f 0 12
s a/f 0 6 b/g 0
f
w a/f 6 6
m a/f
f
""",

"room-short": """
dev 12
n a
n b
w a/f 0 12
s a/f 0 12 b/g 0
w a/f 0 12
m a/f
f
""",

# --- what a line is charged --------------------------------------------------------

"ref-whole": """
dev 32
n a
n b
w a/f 0 10
s a/f 2 3 b/g 0
c a
c b
g b
""",

"ref-once": """
dev 32
n a
w a/f 0 8
s a/f 0 2 a/g 0
s a/f 4 2 a/h 0
c a
""",

"excl-claims": """
dev 32
n a
w a/f 0 8
s a/f 0 4 a/f 4
c a
g a
""",

"excl-lines": """
dev 32
n a
n b
w a/f 0 8
s a/f 0 4 b/g 0
c a
c b
g a
g b
g a,b
""",

# --- stamping ----------------------------------------------------------------------

"stamp-collapse": """
dev 64
n a
w a/f 0 6
w a/g 0 4
c a
p a b
c a
c b
""",

"stamp-diverge": """
dev 64
n a
w a/f 0 6
p a b
w b/f 0 6
c a
c b
f
""",

"stamp-empty": """
dev 32
n a
p a b
c b
w b/f 0 4
c a
c b
""",

"stamp-twice": """
dev 64
n a
w a/f 0 6
p a b
p b c
c a
c b
c c
w c/f 2 2
c a
c c
""",

"drop-keeps": """
dev 64
n a
w a/f 0 6
p a b
w b/f 0 3
f
d b
f
c a
""",

"drop-frees": """
dev 64
n a
n b
w a/f 0 6
s a/f 0 6 b/g 0
d a
f
d b
f
""",

# --- freed by dropping a set -------------------------------------------------------

"gone-set": """
dev 64
n a
w a/f 0 6
p a b
p a c
w c/f 0 6
g a
g b
g a,b
g a,b,c
""",

"gone-one": """
dev 64
n a
n b
w a/f 0 5
w b/g 0 5
s a/f 0 5 b/h 0
c a
g a
g b
g a,b
""",

# --- sharing -----------------------------------------------------------------------

"share-nofree": """
dev 32
n a
n b
w a/f 0 6
w b/g 0 6
f
s a/f 0 6 b/g 0
f
c a
c b
""",

"share-self": """
dev 32
n a
w a/f 0 8
s a/f 0 6 a/f 2
m a/f
f
c a
""",

"share-part": """
dev 32
n a
n b
w a/f 0 9
w b/g 0 9
s a/f 3 3 b/g 3
m b/g
f
c b
""",

# --- truncation, removal, defragmenting --------------------------------------------

"trim-part": """
dev 32
n a
w a/f 0 8
t a/f 5
f
m a/f
t a/f 0
f
""",

"trim-share": """
dev 32
n a
n b
w a/f 0 8
s a/f 0 8 b/g 0
t a/f 2
f
t b/g 2
f
""",

"erase-item": """
dev 32
n a
w a/f 0 6
w a/g 0 6
x a/f
f
x a/g
f
c a
""",

"vac-sole": """
dev 32
n a
w a/f 0 4
w a/g 0 4
w a/h 0 4
x a/g
f
v a/h
m a/h
f
""",

"vac-shared": """
dev 32
n a
w a/f 0 6
p a b
v a/f
m a/f
c a
c b
f
""",

"vac-short": """
dev 12
n a
n b
w a/f 0 8
s a/f 0 8 b/g 0
w a/h 0 4
f
v a/f
m a/f
c a
f
""",

"vac-room": """
dev 12
n a
w a/f 0 8
w a/g 0 4
x a/g
w a/h 0 4
x a/f
w a/f 0 8
f
v a/f
m a/f
f
""",

# --- the picture -------------------------------------------------------------------

"chart-empty": """
dev 16
n a
w a/f 0 4
t a/f 0
m a/f
f
x a/f
m a/f
""",

"chart-merge": """
dev 32
n a
w a/f 0 8
s a/f 0 4 a/g 0
s a/f 4 4 a/g 4
m a/g
m a/f
""",

"lay-straddle": """
dev 32
n a
n b
w a/f 0 4
w a/g 0 3
w a/h 0 4
w a/i 0 3
x a/g
x a/i
f
w a/j 0 12
w a/k 0 6
s a/k 0 6 b/x 0
w a/k 1 1
w a/k 4 1
m a/k
f
""",

# --- the family: a line together with everything stamped from it ---------------------

"fam-leaf": """
# the family of a line with no stamps, and of a leaf, is the line itself
dev 64
n a
w a/f 0 6
w a/g 0 4
c a
u a
p a b
u b
c b
w b/g 0 4
u b
c b
""",

"fam-stamp": """
# a stamp collapses the origin's own exclusive space and leaves its family's where it was
dev 64
n a
w a/f 0 6
c a
u a
p a b
c a
u a
u b
w b/f 0 2
c a
c b
u a
u b
""",

"fam-sum": """
# neither family number is a sum over the members
dev 64
n a
w a/f 0 4
w a/g 0 4
p a b
p a c
w b/f 0 4
w c/g 0 4
c a
c b
c c
u a
u b
u c
g a,b,c
""",

"fam-orphan": """
# a dropped line's stamps count as stamped from the line it came from
dev 64
n a
w a/f 0 4
p a b
p b c
w c/f 0 4
u a
d b
u a
u c
c a
g a,c
""",

"fam-root": """
# a dropped line that came from none leaves its stamps standing alone
dev 64
n a
w a/f 0 4
p a b
p a c
d a
u b
u c
c b
g b,c
""",

"fam-foreign": """
# a line outside the family on a span takes it out of the family's exclusive space
dev 64
n a
w a/f 0 6
p a b
n z
s a/f 0 2 z/g 0
u a
u z
c a
c z
x z/g
u a
""",

"fam-late": """
# two middle lines of a chain go in turn, then a foreign share lands on what they left
dev 96
n a
w a/f 0 6
w a/g 0 6
p a b
w b/f 0 2
p b c
w c/g 0 2
p c d
w d/f 4 2
u a
u b
u c
d b
u a
u c
u d
d c
u a
u d
n z
s d/g 0 2 z/h 0
u a
u d
u z
""",

"fam-split": """
# two sibling stamps share a span their origin left; dropping the origin hands it to its origin
dev 64
n a
w a/f 0 4
p a b
w b/f 0 4
p b c
p b d
w b/f 0 4
u a
u b
d b
u a
u c
u d
g c,d
""",

"fam-reuse": """
# a name made again after a drop is a new line standing alone
dev 64
n a
w a/f 0 4
p a b
d a
n a
w a/f 0 4
u a
u b
c b
""",

"fam-deep": """
# which family a span with several standing lines belongs to, in a nested tree
dev 96
n a
w a/f 0 6
p a b
p b c
p a d
w b/f 0 2
w d/f 4 2
u a
u b
u c
u d
w a/f 0 6
u a
u b
c a
""",

"fam-nosuch": """
dev 32
n a
u z
u a
d a
u a
""",

# --- refusals ----------------------------------------------------------------------

"err-gap": """
dev 32
n a
w a/f 0 4
w a/f 6 2
m a/f
w a/g 3 2
f
s a/f 0 2 a/h 4
""",

"err-range": """
dev 32
n a
w a/f 0 4
w a/f 0 0
t a/f 9
s a/f 2 4 a/g 0
m a/f
f
""",

"err-dup": """
dev 32
n a
n a
w a/f 0 4
p a b
p a b
p c d
c a
""",

"err-nosuch": """
dev 32
n a
w z/f 0 4
c z
g a,z
d z
x a/f
t a/f 2
v a/f
m a/f
p z b
""",

"noroom-hold": """
dev 8
n a
w a/f 0 8
w a/g 0 2
c a
f
m a/g
""",
}

ORDER = sorted(CASES)


def ops(name):
    return [row for row in CASES[name].strip().splitlines() if row.strip()]
