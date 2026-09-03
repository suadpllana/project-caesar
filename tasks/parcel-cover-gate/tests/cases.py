"""The named feeds, one per rule, plus the fences that must keep working.

A case set built one-per-rule is not coverage. What decides whether a case set
is worth anything is whether a *specific* wrong reading survives all of it, so
every feed below is here because it fails one named reading and because the
reference passes it, and `authoring/readings.py` asserts exactly that pairing on
every run. The three fences at the end fail nothing: they are the other half of
the fence, the cases an implementation that has become too careful gets wrong.

Reading the feed language:

    gp <band> <setting...>     name a band
    wr <worker> <setting> <n>  write, standing on whatever that worker shows
    rm <worker> <setting>      the same, with the setting taken away
    pb <worker> <band>         publish the worker's picture of that band
    tk <worker> <parcel>       hand a parcel to a worker
    mg <worker> <setting> <p>  settle one setting against a parcel's version of it
    rd <worker> <setting>      what that worker shows

Parcels are numbered from one in the order they are published.
"""

FEEDS = {}


def _add(name, text):
    FEEDS[name] = text.strip("\n") + "\n"


_add("relay-one", """
gp g1 p
wr wa p 5
pb wa g1
tk wb 1
rd wb p
rd wb q
""")

_add("chain-in-band", """
gp g1 p q
wr wa p 5
wr wa q 6
pb wa g1
tk wb 1
rd wb p
rd wb q
""")

_add("chain-of-three", """
gp g1 p q r
wr wa p 1
wr wa q 2
wr wa r 3
pb wa g1
tk wb 1
rd wb p
rd wb q
rd wb r
""")

_add("rest-outside-band", """
gp g1 p
gp g2 q
wr wa p 5
wr wa q 6
pb wa g2
pb wa g1
tk wb 1
rd wb q
tk wb 2
rd wb p
rd wb q
""")

_add("held-across-ops", """
gp g1 p
gp g2 q
wr wa p 5
wr wa q 6
pb wa g2
tk wb 1
rd wb q
wr wc t 1
wr wc t 2
rd wb q
pb wa g1
tk wb 2
rd wb p
rd wb q
""")

_add("cascade-three-deep", """
gp g1 p
gp g2 q
gp g3 r
wr wa p 1
wr wa q 2
wr wa r 3
pb wa g3
pb wa g2
pb wa g1
tk wb 1
tk wb 2
rd wb p
rd wb q
rd wb r
tk wb 3
rd wb p
rd wb q
rd wb r
""")

_add("whole-or-nothing", """
gp g1 p q
gp g2 r
wr wa p 5
wr wc r 9
pb wc g2
tk wa 1
wr wa q 7
pb wa g1
tk wb 2
rd wb p
rd wb q
""")

_add("whole-later", """
gp g1 p q
gp g2 r
wr wa p 5
wr wc r 9
pb wc g2
tk wa 1
wr wa q 7
pb wa g1
tk wb 2
rd wb p
tk wb 1
rd wb p
rd wb q
rd wb r
""")

_add("fork-not-order", """
gp g1 p
wr wa p 5
pb wa g1
tk wb 1
tk wc 1
wr wb p 6
wr wc p 7
pb wb g1
tk wc 2
rd wc p
rd wb p
""")

_add("fork-both-ways", """
gp g1 p
wr wa p 5
pb wa g1
tk wb 1
tk wc 1
wr wb p 6
wr wc p 7
pb wb g1
pb wc g1
tk wc 2
tk wb 3
rd wb p
rd wc p
""")

_add("settle-then-through", """
gp g1 p
wr wa p 5
pb wa g1
tk wb 1
tk wc 1
wr wb p 6
wr wc p 7
pb wb g1
tk wc 2
mg wc p 2
rd wc p
pb wc g1
tk wb 3
rd wb p
""")

_add("settle-covers-held", """
gp g1 p
gp g2 q
wr wa p 1
pb wa g1
tk wb 1
tk wc 1
wr wb p 2
wr wc p 3
wr wc q 8
pb wc g2
pb wc g1
tk wb 2
rd wb q
tk wb 3
rd wb q
mg wb p 3
rd wb p
rd wb q
""")

_add("settle-far-side", """
gp g1 p
gp g2 q
wr wa p 1
pb wa g1
tk wb 1
tk wc 1
wr wc p 4
wr wc q 9
wr wb p 3
pb wc g1
pb wc g2
tk wb 2
tk wb 3
rd wb p
rd wb q
mg wb p 2
rd wb p
rd wb q
""")

_add("settle-both-parents", """
gp g1 p
gp g2 q
wr wa p 1
pb wa g1
tk wb 1
tk wc 1
wr wb p 2
wr wc p 3
pb wc g1
mg wb p 2
wr wb q 5
pb wb g2
pb wb g1
tk wd 3
tk wd 4
rd wd p
rd wd q
tk wd 1
rd wd p
rd wd q
""")

_add("bag-does-not-cover", """
gp g1 p
gp g2 q
gp g3 r
wr wa r 1
wr wa p 2
wr wa q 3
pb wa g2
pb wa g1
tk wb 1
tk wb 2
rd wb p
rd wb q
rd wb r
""")

_add("older-is-not-cover", """
gp g1 p
gp g2 q
wr wa p 1
pb wa g1
tk wb 1
wr wa p 2
wr wa q 7
pb wa g2
tk wb 2
rd wb p
rd wb q
""")

_add("newer-is-cover", """
gp g1 p
gp g2 q
wr wa p 1
wr wa q 7
pb wa g2
wr wa p 2
pb wa g1
tk wb 2
tk wb 1
rd wb p
rd wb q
""")

_add("gone-shows-x", """
gp g1 p
wr wa p 5
rm wa p
pb wa g1
tk wb 1
rd wb p
""")

_add("gone-is-cover", """
gp g1 p
gp g2 q
wr wa p 5
rm wa p
wr wa q 4
pb wa g1
pb wa g2
tk wb 2
rd wb q
tk wb 1
rd wb p
rd wb q
""")

_add("gone-then-back", """
gp g1 p q
wr wa p 5
wr wa q 1
rm wa p
wr wa p 8
pb wa g1
tk wb 1
rd wb p
rd wb q
""")

_add("part-past-part-new", """
gp g1 p q
wr wa p 1
wr wa q 2
pb wa g1
tk wb 1
wr wa q 3
pb wa g1
tk wb 2
rd wb p
rd wb q
""")

_add("two-takers-diverge", """
gp g1 p
gp g2 q
wr wa p 1
wr wa q 2
pb wa g1
pb wa g2
tk wb 1
tk wb 2
tk wc 2
rd wb p
rd wb q
rd wc p
rd wc q
""")

_add("band-overlap", """
gp g1 p q
gp g2 q r
wr wa p 1
wr wa q 2
wr wa r 3
pb wa g1
pb wa g2
tk wb 2
rd wb q
tk wb 1
rd wb p
rd wb q
rd wb r
""")

_add("wide-picture", """
gp g1 p
gp g2 q r s
wr wa p 1
wr wa q 2
wr wa r 3
wr wa s 4
pb wa g2
tk wb 1
rd wb q
pb wa g1
tk wb 2
rd wb p
rd wb q
rd wb r
rd wb s
""")

_add("nothing-to-add", """
gp g1 p
wr wa p 5
pb wa g1
tk wb 1
rd wb p
tk wb 1
rd wb p
""")

_add("own-parcel", """
gp g1 p q
wr wa p 5
wr wa q 6
pb wa g1
tk wa 1
rd wa p
rd wa q
""")

_add("empty-picture", """
gp g1 p
gp g2 q
wr wa q 3
pb wa g1
tk wb 1
rd wb p
rd wb q
""")

_add("settle-no-entry", """
gp g1 p
gp g2 q
wr wa p 1
wr wb q 2
pb wa g1
mg wb q 1
mg wb p 1
rd wb p
rd wb q
""")

_add("never-heard", """
gp g1 p
wr wa p 5
pb wa g1
rd wb p
rd wb t
tk wb 1
rd wb p
rd wb t
""")

_add("past-entry-not-asked", """
gp g1 p q
gp g2 r
wr wa q 2
wr wa r 9
wr wa p 1
pb wa g1
wr wb p 5
tk wb 1
rd wb p
rd wb q
mg wb p 1
rd wb p
rd wb q
""")

_add("rival-parcels", """
gp g1 p
gp g2 q
wr wa q 9
wr wa p 1
pb wa g2
pb wa g1
tk wb 1
tk wb 2
tk wd 1
tk wd 2
wr wb p 2
wr wd p 3
pb wb g1
pb wd g1
tk wc 3
tk wc 4
rd wc p
tk wc 1
rd wc p
rd wc q
""")
