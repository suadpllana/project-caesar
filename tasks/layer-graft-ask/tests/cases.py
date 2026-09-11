"""The enumerated plans: one per graded decision, plus the must-still-work side of each fence.

Every name below is referred to by `task.toml`'s verification_explanation and by the cheat
write-ups, so a reading and the case that separates it cannot drift apart. The frozen answers
for these live in `seal/gt.json`, which the grader checks the sealed model still reproduces
before it grades anything.
"""

PLANS = {

    # ---- ordinary behaviour that an overconservative rewrite must not break ----

    "plain-put": """lay
put a.b lit 4
put a.c lit 7
lay
put a.b lit 9
ask a.b
ask a.c
ask a.b 1
tot a
""",

    "plain-old-chain": """lay
put x lit 2
lay
put x sum old x lit 1
lay
put x sum old x lit 10
ask x
ask x 2
ask x 1
""",

    "plain-mix": """lay
put s.one lit 3
put s.two lit 4
lay
mix s d
ask d.one
ask d.two
tot d
""",

    "plain-guard-holds": """lay
put flag lit 1
lay
put on lit 8 if flag 1
put off lit 8 if flag 2
ask on
ask off
""",

    # ---- 1. entry order inside a layer ----

    "order-later-wins": """lay
put a lit 1
put a lit 2
put a lit 3
ask a
""",

    "order-cut-then-put": """lay
put a.b lit 1
put a.c lit 2
lay
cut a
put a.b lit 5
ask a.b
ask a.c
tot a
""",

    # ---- 2. a guard is answered before its whole layer ----

    "guard-before-cut": """lay
put a lit 1
lay
put keep lit 3
cut a
put late lit 7 if a 1
ask late
ask a
""",

    "guard-before-put": """lay
put a lit 1
lay
cut a
put late lit 7 un a
ask late
""",

    # ---- 3. a guard is answered as if the plan stopped at its own layer ----

    "guard-own-stop": """lay
put a lit 1
lay
put b now a
lay
put c lit 9 if b 1
lay
put a lit 5
ask c
ask b
""",

    "guard-un-on-loop": """lay
put spin sum now spin lit 1
lay
put a lit 4 un spin
put b lit 4 if spin 1
ask spin
ask a
ask b
""",

    # ---- 4. a query that names a layer counts only those layers, values included ----

    "stop-value": """lay
put a lit 1
lay
put b now a
lay
put a lit 5
ask b
ask b 2
ask a 1
""",

    "stop-zero": """lay
put a lit 1
ask a 0
tot a 0
ask a
""",

    # ---- 5. a removal takes everything under the path ----

    "cut-subtree": """lay
put a.b.c lit 1
put a.b.d lit 2
put a.e lit 3
lay
cut a.b
ask a.b.c
ask a.e
tot a
tot a 1
""",

    # ---- 6. a copy replaces the destination, and reads its sources first ----

    "mix-replaces": """lay
put s.one lit 1
put d.gone lit 2
lay
mix s d
ask d.gone
ask d.one
tot d
""",

    "mix-into-self": """lay
put a.z lit 1
put a.y.x lit 2
lay
mix a a.b
lay
mix a a.c
tot a
ask a.c.b.z
ask a.b.z
tot a 2
""",

    "mix-src-under-dst": """lay
put a.b.c lit 1
put a.d lit 2
lay
mix a.b a
tot a
ask a.d
ask a.c
""",

    "mix-empty-source": """lay
put d.one lit 1
lay
mix s d
tot d
ask d.one
""",

    # ---- 7. a copy carries definitions, not the values it found ----

    "carry-follows-now": """lay
put q lit 2
lay
put p.a sum now q lit 10
lay
mix p r
lay
put q lit 9
ask r.a
ask r.a 3
ask p.a
""",

    # ---- 8. a carried definition keeps the layer that wrote it ----

    "carry-keeps-old": """lay
put q lit 2
lay
put p.a sum old q lit 10
lay
put q lit 7
lay
mix p r
lay
put q lit 9
ask r.a
ask p.a
ask r.a 4
""",

    "carry-same-both-ends": """lay
put q lit 5
lay
put p.a sum now q lit 1
lay
mix p r
ask p.a
ask r.a
""",

    # ---- 9. circularity belongs to the definition and the stop, not to the text ----

    "loop-now-self": """lay
put x sum now x lit 1
ask x
""",

    "old-self-ok": """lay
put x lit 2
lay
put x sum old x lit 1
ask x
ask x 1
""",

    "loop-moves-with-stop": """lay
put a.x sum now a.x lit 1
lay
mix a b
lay
put a.x lit 5
ask a.x 1
ask b.x
ask a.x
""",

    "loop-two-paths": """lay
put y now z
put z now y
ask y
ask z
""",

    # ---- 10. absent and circular are distinct, and the left side decides ----

    "err-left-gone": """lay
put e sum now e lit 1
lay
put f sum now nope now e
ask f
""",

    "err-left-loop": """lay
put e sum now e lit 1
lay
put g sum now e now nope
ask g
""",

    # ---- 11. a count reports only the paths holding a definition ----

    "count-defined": """lay
put a.b.c lit 1
put a.b.d lit 2
lay
put a lit 3
tot a
tot a.b
tot a 1
tot nothing
""",

    # ---- 12. pick tests the definition, takes one side, counts as the question does ----

    "pick-defined-but-gone": """lay
put hole now missing
lay
put out pick hole lit 1 lit 2
put also lit 5 un hole
ask out
ask also
ask hole
""",

    "pick-under-not-at": """lay
put a.b lit 1
lay
put out pick a lit 1 lit 2
ask out
""",

    "pick-side-not-asked": """lay
put b sum now a lit 1
put a pick nothere now b lit 5
ask a
ask b
""",

    "pick-lazy-side": """lay
put spin sum now spin lit 1
put safe lit 3
lay
put out pick safe lit 7 now spin
ask out
""",

    "pick-at-the-stop": """lay
put out pick late lit 1 lit 2
lay
put late lit 9
ask out
ask out 1
""",

    # ---- arithmetic, both operators, negatives ----

    "sum-top-negative": """lay
put a lit -6
put b lit 4
lay
put s sum now a now b
put t top now a now b
ask s
ask t
""",
}
