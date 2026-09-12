"""The enumerated programs: one per graded decision, and both sides of every fence.

Each is small enough to work through by hand, and each was written for one rule. The names say
which. Where a rule has a side that must still work - a claim that must not report a second
give, a member that must stay taken after the use that pulled it left, a proposal of an image
that must still count what the roots reach - the must-still-work side is a case of its own, so
an engine that turns conservative fails as loudly as one that is careless.
"""

PROGS = {

    # --- an ordinary link, so the everyday path is fenced too --------------------------
    "plain-link": """
u a
p 10 -
g f s
r g s
u b
p 20 -
g g s
b lib b
root f
link a lib
at f
at g
img
""",

    # --- claim keys -------------------------------------------------------------------

    # A part whose key is held is dropped, and the uses it would have brought never enter,
    # so the member that would have satisfied them is not taken.
    "claim-drop": """
u a
p 10 kg
g f s
r h s
u c
p 5 -
g h s
b lib c
u d
p 12 kg
g f s
r j s
u e
p 7 -
g j s
b lib2 e
root f
link a lib d lib2
at f
img
""",

    # Two parts of one unit under one key: the second is dropped by the first.
    "claim-same-unit": """
u a
p 10 kg
g f s
r h s
p 6 kg
g h s
u c
p 5 -
g h s
b lib c
root f
link a lib
at f
at h
img
""",

    # The ordinary case: two units give one name under one key and it is not a second give.
    "claim-no-dup": """
u top
p 3 -
g start s
r f s
r q s
u one
p 5 kg
g f s
u two
p 6 kg
g f s
p 4 -
g q s
b lib one two
root start
link top lib
at f
img
""",

    # --- displacement -----------------------------------------------------------------

    # A unit off the input list takes a key back from a bundle member: the displaced part's
    # give and use both leave, and the member its use pulled stays taken and is pruned.
    "shift-key": """
u top
p 3 -
g start s
r f s
u c
p 5 kg
g f s
r h s
u h1
p 4 -
g h s
b lib c h1
u d
p 12 kg
g f s
r j s
u e
p 7 -
g j s
b lib2 e
root start
link top lib d lib2
at f
at h
at j
img
""",

    # A key held by a unit off the input list is never taken from it.
    "shift-firm": """
u top
p 3 -
g start s
r f s
u first
p 9 kg
g f s
u later
p 14 kg
g z s
r q s
u qq
p 6 -
g q s
b lib qq
root start
link top first later lib
at f
at z
img
""",

    # A member taken later does not displace the claim of a member taken earlier.
    "shift-second": """
u top
p 3 -
g start s
r f s
r w s
u one
p 5 kg
g f s
u two
p 11 kg
g w s
b lib one two
root start
link top lib
at f
at w
img
""",

    # The displacement puts a name back into the wanted set and the next bundle supplies it.
    "shift-again": """
u top
p 3 -
g start s
r f s
r w1 s
u c
p 5 kg
g f s
g w2 s
u w1u
p 4 -
g w1 s
b lib c w1u
u d
p 12 kg
g z s
u fx
p 8 -
g f s
u e2
p 6 -
g w2 s
b lib2 fx e2
root start
link top lib d lib2
at f
at w2
img
""",

    # The input list is walked once: a name wanted again by a displacement is not carried back
    # to a bundle that is already behind it, however well that bundle could have supplied it.
    "shift-earlier": """
u top
p 3 -
g start s
r f s
u c
p 5 kg
g f s
u alt
p 9 -
g f s
b lib c alt
u d
p 12 kg
g w s
u e
p 4 -
g q s
b lib2 e
root start
link top lib d lib2
at f
img
""",

    # The displaced part's use leaves with it, so the member of the next bundle that would
    # have answered it is not taken.
    "shift-use-gone": """
u top
p 3 -
g start s
r f s
u c
p 5 kg
g f s
r u1 s
b lib c
u d
p 12 kg
g f s
u e
p 7 -
g u1 s
b lib2 e
root start
link top lib d lib2
at f
at u1
img
""",

    # The first strong give leaves and the name falls to the next one, with nothing printed.
    "shift-rebind": """
u top
p 3 -
g start s
r f s
r w s
u c
p 5 kg
g f s
u c2
p 7 -
g w s
g f s
b lib c c2
u d
p 12 kg
g y s
root start
link top lib d
at f
at w
img
""",

    # --- weak gives and weak uses -----------------------------------------------------

    # A weak give does not settle a name, so the member that gives it strongly is taken.
    "weak-give": """
u top
p 3 -
g start s
r f s
r m s
u wk
p 4 -
g m s
g f w
u st
p 9 -
g f s
b lib wk st
root start
link top lib
at f
img
""",

    # With no strong give anywhere the name stands on the first weak one.
    "weak-bind": """
u top
p 3 -
g start s
r f s
r m s
u wk
p 4 -
g m s
g f w
u wk2
p 8 -
g f w
b lib wk wk2
root start
link top lib
at f
img
""",

    # A weak use wants nothing, so nothing is taken for it.
    "weak-use-quiet": """
u top
p 3 -
g start s
r f w
r m s
u m1
p 4 -
g m s
u f1
p 9 -
g f s
b lib f1 m1
root start
link top lib
at f
at m
img
""",

    # A weak use reaches nothing: the part it names is out of the image.
    "weak-reach": """
u top
p 2 -
g start s
r a1 s
r c1 s
u m
p 3 -
g a1 s
r b1 w
u n
p 4 -
g c1 s
p 6 -
g b1 s
b lib m n
root start
link top lib
at b1
img
""",

    # --- a second strong give ---------------------------------------------------------

    "dup-report": """
u top
p 3 -
g start s
r f s
r q s
u c
p 5 -
g f s
u c2
p 6 -
g q s
g f s
b lib c c2
root start
link top lib
at f
img
""",

    # --- which member a bundle gives up ------------------------------------------------

    # The member taken is the first in member order, not the one for the name wanted first.
    "take-order": """
u top
p 2 -
g start s
r n1 s
r n2 s
u m1
p 3 -
g n2 s
u m2
p 4 -
g n1 s
b lib m1 m2
root start
link top lib
img
""",

    # A take wants a name an earlier member gives, so the scan starts again at the first.
    "take-restart": """
u top
p 2 -
g start s
r n2 s
u m1
p 3 -
g n1 s
u m2
p 4 -
g n2 s
r n1 s
b lib m1 m2
root start
link top lib
at n1
img
""",

    # A unit named twice on the input list is loaded once.
    "take-once": """
u a
p 10 -
g f s
r g s
u b
p 20 -
g g s
b lib b
root f
link a a lib
at f
at g
img
""",

    # A member already in is passed over rather than taken again, even where it is the first
    # member giving the name and the part that would have given it was dropped for a key.
    "take-loaded": """
u top
p 2 -
g start s
r n1 s
u pre
p 6 kg
g z s
u m1
p 3 kg
g n1 s
u m2
p 4 -
g n1 s
b lib m1 m2
root start
link top pre m1 lib
at n1
at z
img
""",

    # --- a group of bundles ------------------------------------------------------------

    "group-pass": """
u top
p 2 -
g start s
r p1 s
u m1
p 3 -
g p1 s
r p2 s
u m2
p 4 -
g p2 s
r p3 s
u m3
p 5 -
g p3 s
b b1 m1 m3
b b2 m2
root start
link top ( b1 b2 )
at p3
img
""",

    # Outside a group the input list is walked once, so the later bundle is never re-entered.
    "group-none": """
u top
p 2 -
g start s
r p1 s
u m1
p 3 -
g p1 s
r p2 s
u m2
p 4 -
g p2 s
r p3 s
u m3
p 5 -
g p3 s
b b1 m1 m3
b b2 m2
root start
link top b1 b2
at p3
img
""",

    # --- spares -------------------------------------------------------------------------

    # The largest size spared wins, and the first unit in load order that spared it at that
    # size is the one it stands against.
    "spare-size": """
u a
p 4 -
g start s
r s1 s
t s1 16
u b2
p 5 -
g z s
t s1 40
u c3
p 6 -
g y s
t s1 40
root start
link a b2 c3
at s1
img
""",

    # A give from a member pulled late cancels the spare outright.
    "spare-cancel": """
u a
p 4 -
g start s
r s1 s
r k1 s
t s1 40
u m
p 9 -
g k1 s
g s1 s
b lib m
root start
link a lib
at s1
img
""",

    # A spare wants a name on its own, with nothing using it.
    "spare-want": """
u a
p 4 -
g start s
t s1 24
u m
p 9 -
g s1 s
b lib m
root start
link a lib
at s1
img
""",

    # A placed name counts only where something reaches it.
    "spare-reach": """
u a
p 4 -
g start s
t s1 24
t s2 30
p 6 -
r s2 s
root start
hold a 1
link a
at s1
at s2
img
""",

    # --- the prune ----------------------------------------------------------------------

    # A kept part nothing reaches is out of the image and the name it gives binds to nothing.
    "prune-drop": """
u top
p 2 -
g start s
r a1 s
u m
p 3 -
g a1 s
p 7 -
g b1 s
b lib m
root start
link top lib
at a1
at b1
img
""",

    # A held part is a root of its own.
    "prune-hold": """
u top
p 2 -
g start s
r a1 s
u m
p 3 -
g a1 s
p 7 -
g b1 s
r c1 s
u n
p 5 -
g c1 s
b lib m n
root start
hold m 1
link top lib
at b1
at c1
img
""",

    # Two roots, and a part reached only through the second.
    "prune-root": """
u top
p 2 -
g start s
r a1 s
p 8 -
g other s
r d1 s
u m
p 3 -
g a1 s
u n
p 5 -
g d1 s
b lib m n
root start
root other
link top lib
at d1
img
""",

    # --- the input list is an order ------------------------------------------------------

    # The same units and bundles in a different order settle differently.
    "order-list": """
u top
p 3 -
g start s
r f s
u c
p 5 kg
g f s
r h s
u h1
p 4 -
g h s
b lib c h1
u d
p 12 kg
g f s
root start
link top d lib
at f
at h
img
""",
}

ORDER = tuple(sorted(PROGS))


def ops(name):
    """The program, as the lines a run would read."""
    return [line for line in PROGS[name].strip().splitlines() if line.strip()]
