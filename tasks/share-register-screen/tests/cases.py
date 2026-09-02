"""The enumerated registers, one per rule, each named for the reading it exists to fail.

Every rule the determination turns on is pinned by a case here, and both sides of every
fence are present: for each company that must be on the list there is one that must stay
off for a reason a nearby wrong reading would get backwards.

Coverage on paper is not coverage. authoring/readings.py writes down the wrong readings
themselves and tools/readingcheck.py runs them, which is what says a case set separates a
reading rather than merely mentioning its subject.
"""

CASES = [
    ("direct-majority", """pg h1
co k1 3
cl k1 o 1
is k1 o 710 h1
is k1 o 290 h2
"""),
    ("direct-minority", """pg h1
co k1 5
cl k1 o 1
is k1 o 190 h1
is k1 o 810 h2
"""),
    ("one-step-chain", """pg h1
co k1 3
cl k1 o 1
is k1 o 730 h1
is k1 o 270 h2
co k2 3
cl k2 o 1
is k2 o 910 k1
is k2 o 130 h3
"""),
    ("backward-chain", """pg h1
co k1 3
cl k1 o 1
is k1 o 910 k2
is k1 o 130 h3
co k2 3
cl k2 o 1
is k2 o 730 h1
is k2 o 270 h2
"""),
    ("revisit-after-growth", """pg h1
co k1 3
cl k1 o 1
is k1 o 130 h1
is k1 o 190 k3
is k1 o 290 h5
co k2 3
cl k2 o 1
is k2 o 130 h1
is k2 o 190 k1
is k2 o 290 h6
co k3 3
cl k3 o 1
is k3 o 730 h1
is k3 o 270 h7
"""),
    ("two-hands-carry", """pg h1
pg h2
co k1 3
cl k1 o 1
is k1 o 130 h1
is k1 o 190 h2
is k1 o 290 h3
"""),
    ("two-hands-fall-short", """pg h1
pg h2
co k1 3
cl k1 o 1
is k1 o 130 h1
is k1 o 170 h2
is k1 o 730 h4
"""),
    ("hand-of-one", """pg h1
co k1 3
cl k1 o 1
is k1 o 610 h1
is k1 o 290 h2
is k1 o 130 h3
"""),
    ("added-company-joins-hand", """pg h1
co k1 3
cl k1 o 1
is k1 o 130 h1
is k1 o 190 k2
is k1 o 290 h3
co k2 3
cl k2 o 1
is k2 o 730 h1
is k2 o 270 h4
"""),
    ("carried-then-carries", """pg h1
pg h2
co k1 3
cl k1 o 1
is k1 o 130 h1
is k1 o 190 h2
is k1 o 290 h3
co k2 3
cl k2 o 1
is k2 o 910 k1
is k2 o 130 h4
"""),
    ("exactly-half", """pg h1
co k1 2
cl k1 o 1
is k1 o 530 h1
is k1 o 470 h2
"""),
    ("board-of-two", """pg h1
co k1 2
cl k1 o 1
is k1 o 890 h1
is k1 o 110 h2
"""),
    ("majority-votes-minority-board", """pg h1
co k1 4
cl k1 o 1
is k1 o 510 h1
is k1 o 490 h2
"""),
    ("minority-votes-majority-board", """pg h1
co k1 3
cl k1 o 1
is k1 o 430 h1
is k1 o 190 h2
is k1 o 170 h3
is k1 o 130 h4
"""),
    ("nominee-brings-votes", """pg h1
co k1 3
cl k1 o 1
is k1 o 710 n1
is k1 o 290 h2
nm n1 h1
"""),
    ("nominee-takes-votes-away", """pg h1
co k1 3
cl k1 o 1
is k1 o 710 h1
is k1 o 290 h2
nm h1 h9
"""),
    ("nominee-chain", """pg h1
co k1 3
cl k1 o 1
is k1 o 730 n2
is k1 o 270 h2
nm n2 n3
nm n3 h1
"""),
    ("ended-arrangement", """pg h1
co k1 3
cl k1 o 1
is k1 o 710 h1
is k1 o 290 h2
nm h1 h9
nx h1
"""),
    ("treasury-silent", """pg h1
co k1 3
cl k1 o 1
is k1 o 430 h1
is k1 o 730 h2
mv k1 o 530 h2 k1
"""),
    ("transfer-moves-a-hand", """pg h1
co k1 3
cl k1 o 1
is k1 o 710 h1
is k1 o 290 h2
mv k1 o 530 h1 h2
"""),
    ("class-weights", """pg h1
co k1 3
cl k1 o 1
cl k1 p 10
is k1 p 73 h1
is k1 o 290 h2
"""),
    ("vacant-seats", """pg h1
co k1 5
cl k1 o 1
is k1 o 910 h1
"""),
    ("ring-of-two", """pg h1
co k1 3
cl k1 o 1
is k1 o 530 k2
is k1 o 470 h2
co k2 3
cl k2 o 1
is k2 o 530 k1
is k2 o 470 h3
"""),
    ("own-shares-through-a-nominee", """pg h1
co k1 3
cl k1 o 1
is k1 o 410 h1
is k1 o 290 h2
is k1 o 530 n1
nm n1 k1
"""),
    ("own-shares-through-a-chain", """pg h1
co k1 3
cl k1 o 1
is k1 o 410 h1
is k1 o 290 h2
is k1 o 530 n2
nm n2 n3
nm n3 k1
"""),
    ("own-shares-against-the-list", """pg h1
pg h2
co k1 3
cl k1 o 1
is k1 o 130 h1
is k1 o 190 h2
is k1 o 290 h3
is k1 o 470 n1
nm n1 k1
"""),
    ("nominee-for-a-company-elsewhere", """pg h1
co k1 3
cl k1 o 1
is k1 o 730 h1
is k1 o 270 h2
co k2 3
cl k2 o 1
is k2 o 190 n1
is k2 o 170 h3
is k2 o 290 h4
nm n1 k1
"""),
]
