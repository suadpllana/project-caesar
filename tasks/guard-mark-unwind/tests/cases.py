"""The enumerated set: one program per rule, aimed where a plausible reading diverges.

Each entry names the reading it is built to fail. The randomized set in gen.py covers the
combinations nobody thought of; this set makes sure the individual rules are pinned, and
makes a failure report legible - a submission that fails only band-restamp has a different
bug from one that fails only bundle-order.

Fence cases are marked MUST-WORK: they exist so that an implementation which over-cancels
(cuts whenever anything anywhere is marked, refuses to let a shielded fiber finish, stops
a band on any mark) fails just as hard as one that under-cancels.
"""

PROGS = {}
NOTE = {}


def case(name, note, text):
    PROGS[name] = text.strip("\n")
    NOTE[name] = note


case("no-mark-no-cut", "MUST-WORK: nothing marked, every block runs and the fiber ends ok", """
:main
G 1 -1 0
S 1
W 2
G 2 -1 0
S 2
P
E
S 3
E
S 4
""")

case("outer-wins", "delivery goes to the outermost marked guard, not the innermost: "
     "attributing inward lets the fiber emit a token inside a guard already marked", """
:main
G 1 -1 0
G 2 -1 0
M 1
M 2
P
S 1
E
S 2
E
S 3
""")

case("outer-wins-deep", "same, three deep, with the middle guard also marked", """
:main
G 1 -1 0
G 2 -1 0
G 3 -1 0
M 2
M 3
S 1
P
S 2
E
S 3
E
S 4
E
S 5
""")

case("shield-owns-mark", "a shield hides the marks outside its guard, never the mark on "
     "that guard itself", """
:main
G 1 -1 1
M 1
P
S 1
E
S 2
""")

case("shield-hides-outer", "MUST-WORK: the fiber runs to the end of the shielded region "
     "with an outer guard marked the whole time", """
:main
G 1 -1 0
G 2 -1 1
M 1
S 1
P
S 2
W 2
S 3
E
S 4
E
S 5
""")

case("shield-drop", "dropping the shield puts the outer mark back in view at the next "
     "checkpoint, because marks are sticky rather than consumed", """
:main
G 1 -1 0
G 2 -1 1
M 1
P
S 1
H 0
S 2
P
S 3
E
S 4
E
S 5
""")

case("cleanup-outside", "a cleanup block runs after its own guard has closed, so its "
     "checkpoints answer to the enclosing chain and not to the guard it belongs to", """
:main
G 1 -1 0
G 2 -1 0
A
S 1
P
S 2
Z
M 2
P
S 3
E
S 4
E
S 5
""")

case("cleanup-under-outer-mark", "the same cleanup block with the enclosing guard marked: "
     "the block is abandoned at its first checkpoint", """
:main
G 1 -1 0
G 2 -1 0
A
S 1
P
S 2
Z
M 1
P
S 3
E
S 4
E
S 5
""")

case("cleanup-shielded", "MUST-WORK: shielding the enclosing guard from inside the "
     "cleanup block lets the block finish under an outer mark", """
:main
G 1 -1 0
G 2 -1 0
A
H 1
S 1
P
S 2
Z
M 1
P
S 3
E
S 4
E
S 5
""")

case("cleanup-raises", "an exception raised inside a cleanup block replaces the one "
     "already travelling, rather than being dropped for it", """
:main
G 1 -1 0
G 2 -1 0
A
S 1
F
Z
M 1
P
S 2
E
S 3
E
S 4
""")

case("band-holds", "a fiber standing at the close of a band cannot leave while a child "
     "is alive, whatever mark has reached it", """
:main
G 1 -1 0
B 2
N kid
M 2
X
S 1
E
S 2
:kid
S 10
W 3
S 11
""")

case("band-restamp", "the mark that stood when the fiber first tried to leave the band "
     "is not the mark it leaves under: the child raises a new one while it waits", """
:main
G 1 -1 0
B 2
N kid
M 2
X
S 1
E
S 2
:kid
G 5 -1 1
S 10
W 3
M 1
W 1
S 11
E
""")

case("stale-stamp", "the guard a cut was raised for is not the guard it comes to rest "
     "at: a sibling marks an enclosing guard while the fiber is parked at a band it "
     "cannot leave, and no checkpoint stands between that mark and the boundary", """
:main
G 1 -1 0
G 2 -1 0
B 3
N kid
M 2
P
S 1
X
S 2
E
S 3
E
S 4
:kid
G 5 -1 1
S 10
W 2
M 1
W 2
S 11
E
""")

case("band-snag", "a fiber unwinding into a band it owns marks the band's own guard, so "
     "the children stop instead of running on under an exception already in flight", """
:main
B 2
N kid
S 1
F
X
S 2
:kid
S 10
W 4
S 11
""")

case("outer-outranks-bundle", "a mark on a guard enclosing the band outranks what the "
     "children collected, and the cut leaves on its own", """
:main
G 1 6 0
B 2
N kid
X
S 1
E
S 2
:kid
G 5 -1 1
W 10
F
E
""")

case("band-own-mark", "the band's own mark is what the close was for, so nothing leaves "
     "when there is nothing to report", """
:main
G 1 -1 0
B 2
N kid
X
S 1
E
S 2
:kid
W 1
M 2
W 2
S 10
""")

case("bundle-order", "collected payloads leave in the order the children ended, which is "
     "not the order they were made", """
:main
B 2
N slow
N fast
X
S 1
:slow
G 5 -1 1
W 5
F
E
:fast
W 1
F
""")

case("shielded-child-survives", "MUST-WORK: a child shielded from the band's mark runs "
     "to its own end and its tokens stand", """
:main
B 2
N tough
N boom
X
S 1
:tough
G 5 -1 1
S 10
W 4
S 11
E
:boom
W 1
F
""")

case("nested-band", "a bundle leaving an inner band is collected by the outer one and "
     "leaves again with the payloads it carried", """
:main
B 1
N mid
X
S 1
:mid
B 2
N low
W 1
X
S 10
:low
W 3
F
""")

case("deadline-at-entry", "a guard whose deadline has already passed when it is opened "
     "is marked there and then, not at the next advance of the clock", """
:main
W 3
G 1 0 0
S 1
P
S 2
E
S 3
""")

case("deadline-wakes-sleeper", "a deadline landing on a sleeping fiber wakes it at the "
     "deadline rather than at the end of its wait", """
:main
G 1 2 0
S 1
W 9
S 2
E
S 3
""")

case("deadline-elsewhere", "MUST-WORK: a deadline on a guard the fiber is not inside "
     "leaves it alone", """
:main
B 1
N timed
N sleeper
X
S 1
:timed
G 5 2 0
W 6
S 10
E
:sleeper
W 5
S 20
W 5
S 21
""")

case("spawn-inherits-band", "MUST-WORK: a child answers to the chain that stood when the "
     "band was opened, not to the guards its parent opened afterwards", """
:main
B 1
N kid
G 5 -1 0
M 5
P
S 1
E
X
S 2
:kid
S 10
W 3
S 11
""")

case("cross-fiber-mark", "a child marking a guard of its parent reaches the parent while "
     "it sleeps", """
:main
G 1 -1 0
B 2
N kid
W 8
S 1
X
S 2
E
S 3
:kid
W 2
M 1
W 9
S 10
""")

case("err-passes-guards", "an error is not a cut: no guard takes it, marked or not", """
:main
G 1 -1 0
M 1
G 2 -1 0
S 1
F
E
S 2
E
S 3
""")

case("zero-wait", "a wait of zero is still a checkpoint", """
:main
G 1 -1 0
M 1
S 1
W 0
S 2
E
S 3
""")

case("mark-twice", "MUST-WORK: marking a guard that is already marked changes nothing "
     "and does not report a second time", """
:main
G 1 -1 0
M 1
M 1
S 1
P
S 2
E
S 3
""")


case("unmarked-guard-passes-it", "only a marked guard takes a cut: the band's own guard is "
     "marked and popped without absorbing it, so the cut reaches an unmarked enclosing guard "
     "with nothing visible marked, goes straight through, and leaves with the fiber", """
:main
G 1 -1 0
A
Z
B 2
N p1
W 2
X
G 5 2 1
G 6 -1 0
E
E
E
:p1
G 3 3 1
A
M 2
Z
G 4 -1 0
E
E
""")
