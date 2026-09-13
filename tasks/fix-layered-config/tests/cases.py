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

# 2026-09-13 mapped binding contract. Existing hand cases remain above.
PLANS.update({
    'map-capture-compose-mix': 'lay\nput src.k lit 2\nput dst.k lit 10\nput end.k lit 40\nlay\nput src.v sum now src.k old src.k\nput dst.k lit 20\nmap src dst\nput dst.k lit 30\nmap dst end\nput end.k lit 60\nmix dst keep\nask src.v\nask dst.v\nask end.v\nask keep.v\nask dst.k\ntot keep\n',
    'map-sparse-put-escapes': 'lay\nput src.k lit 2\nput src.v now src.k\nput src.deep.v now src.k\nmap src dst\nput dst.deep.v now src.k\nput src.k lit 7\nput dst.k lit 9\nask dst.v\nask dst.deep.v\nask src.deep.v\ntot dst\n',
    'map-capture-before-clear': 'lay\nput src.k lit 2\nput src.v old src.k\nput dst.k lit 10\nlay\nmap src dst\nask src.v\nask dst.v\nask dst.k\n',
    'map-old-external-capture': 'lay\nput ext lit 3\nlay\nput src.v old ext\nput ext lit 7\nmap src dst\nput ext lit 11\nask src.v\nask dst.v\nask ext\n',
    'map-old-transitive-view': 'lay\nput src.k lit 2\nput dst.k lit 10\nlay\nput dst.proxy now dst.k\nput src.v old src.proxy\nput dst.k lit 20\nmap src dst\nput dst.k lit 30\nask dst.v\nask src.v\nask dst.proxy\n',
    'map-old-transitive-pick': 'lay\nput src.v old src.proxy\nput dst.proxy pick dst.flag lit 6 lit 8\nput dst.flag lit 1\nlay\nmap src dst\nask dst.v\nask dst.flag\n',
    'map-guard-before-layer': 'lay\nput flag lit 1\nput src.v lit 5\nput dst.v lit 9\nlay\nput flag lit 2\nmap src dst if flag 1\nmap src skip if flag 2\nmap src absent un flag\nask dst.v\nask skip.v\nask absent.v\n',
    'map-guard-history': 'lay\nput ext lit 3\nput flag lit 1\nlay\nput src.v old ext\nput ext lit 7\nmap src dst if flag 1\nput ext lit 11\nlay\ncut flag\nput yes lit 19 if dst.v 7\nput no lit 23 if dst.v 11\nask yes\nask no\nask dst.v\n',
    'map-overlap-source-under-dest': 'lay\nput a.b.v lit 3\nput a.z lit 7\nlay\nmap a.b a\nask a.v\nask a.b.v\ntot a\ntot a 1\n',
    'map-overlap-equal': 'lay\nput a.v lit 3\nmap a a\nask a.v\ntot a\n',
    'map-overlap-dest-under-source': 'lay\nput a.k lit 2\nput a.v old a.k\nput a.b.k lit 9\nput a.b.z lit 8\nlay\nmap a a.b\nask a.b.v\nask a.b.k\nask a.b.z\nask a.b.b.z\ntot a\ntot a.b\n',
    'map-empty-source-clears': 'lay\nput dst.x lit 7\nlay\nmap absent dst\nask dst.x\ntot dst\n',
    'map-prefix-boundary': 'lay\nput src.k lit 2\nput srcside.k lit 11\nput src.v sum now src.k now srcside.k\nmap src dst\nput src.k lit 3\nput dst.k lit 7\nput srcside.k lit 13\nask src.v\nask dst.v\n',
    'map-root-operand': 'lay\nput src lit 2\nput src.v now src\nmap src dst\nput src lit 3\nput dst lit 7\nask src.v\nask dst.v\ntot dst\n',
    'map-dormant-pick-arms': 'lay\nput src.k lit 2\nput src.v pick src.flag now src.k now src.other\nmap src dst\nlay\nput src.flag lit 1\nput src.k lit 3\nput dst.other lit 9\nask src.v\nask dst.v\nask dst.v 1\n',
    'map-pick-presence-not-value': 'lay\nput src.hole now missing\nput src.v pick src.hole lit 4 now src.v\nmap src dst\ncut src.hole\nask dst.v\nask src.v\nask dst.hole\n',
    'map-pick-exact-presence': 'lay\nput src.flag.child lit 1\nput src.v pick src.flag lit 3 lit 7\nmap src dst\nput src.flag lit 2\nask src.v\nask dst.v\n',
    'map-distinct-map-identities': 'lay\nput ext lit 2\nput src.v old ext\nlay\nput ext lit 3\nmap src a\nput ext lit 5\nmap src b\nput ext lit 7\nask b.v\nask a.v\nask b.v\nask src.v\n',
    'map-alias-preserved-in-source': 'lay\nput src.k lit 2\nput src.a.v sum now src.k old ext\nmix src.a src.b\nput ext lit 3\nmap src dst\nput dst.k lit 7\nput ext lit 9\nask dst.a.v\nask dst.b.v\nask src.a.v\nask src.b.v\n',
    'map-mix-retains-identity-and-paths': 'lay\nput src.k lit 2\nput src.v now src.k\nmap src dst\nmix dst keep\nput dst.k lit 7\nput keep.k lit 11\nput src.k lit 13\nask src.v\nask dst.v\nask keep.v\n',
    'map-loop-cache-separation': 'lay\nput src.k lit 2\nput src.v now src.k\nmap src dst\nput dst.k now dst.v\nask dst.v\nask src.v\nask dst.k\nask src.v\n',
    'map-loop-cache-separation-reverse': 'lay\nput src.k lit 2\nput src.v now src.k\nmap src dst\nput dst.k now dst.v\nask src.v\nask dst.v\nask src.v\n',
    'map-error-order': 'lay\nput src.spin now src.spin\nput src.left sum now src.missing now src.spin\nput src.right top now src.spin now src.missing\nmap src dst\nput src.spin lit 7\nask dst.left\nask dst.right\nask src.left\nask src.right\n',
    'map-query-history-capture': 'lay\nput ext lit 3\nput src.k lit 2\nput src.v sum now src.k old ext\nlay\nput ext lit 5\nmap src dst\nput dst.k lit 7\nlay\nput dst.k lit 11\nput ext lit 13\nask dst.v 1\nask dst.v 2\nask dst.v\nask src.v\ntot dst 1\n',
    'map-put-old-is-layer-start': 'lay\nput ext lit 2\nput src.k lit 3\nput src.v old ext\nlay\nput ext lit 5\nmap src dst\nput dst.f old ext\nput ext lit 9\nask dst.v\nask dst.f\n',
    'map-cut-shared-descendant': 'lay\nput src.a.x lit 2\nput src.b.x lit 3\nmap src dst\nmap dst end\ncut dst.a\nput dst.b.x lit 11\nask src.a.x\nask dst.a.x\nask end.a.x\nask src.b.x\nask dst.b.x\nask end.b.x\ntot src\ntot dst\ntot end\n',
    'map-composed-prefix-reentry': 'lay\nput a.k lit 2\nput a.v now a.k\nmap a b\nmap b a\nput a.k lit 11\nput b.k lit 7\nask a.v\nask b.v\n',
    'map-old-loop-in-captured-view': 'lay\nput src.v old src.x\nput dst.x now dst.y\nput dst.y now dst.x\nlay\nmap src dst\nput dst.x lit 7\nput dst.y lit 9\nask dst.v\nask dst.x\nask src.v\n',
})
