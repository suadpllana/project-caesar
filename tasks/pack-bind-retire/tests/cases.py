"""The enumerated cases.

Each entry after the three shipped ones is a counterexample to one plausible-but-wrong
reading of the contract, shrunk by hand so that a failure names the rule that broke rather
than reporting that some fraction of random scripts came out wrong. The names say which rule
each pins; `authoring/pack-bind-retire/readings.py` holds the reading each one separates.
"""

FIXED = {

"boot": """pk shell
rq draw
rq store
nd paint
nd disk
st draw
pk paint
pv draw
pv blit
rq store
pk disk
pv store
pv flush
pk theme
pv draw
ld theme open
ld shell open
us shell draw
us shell store
dp theme
us paint store
""",

"swap": """pk editor
rq lint
rq fmt
nd tools
st lint
pk tools
pv lint
pv fmt
wk cache
pk fast
pv lint
pv cache
ld editor open
dp tools
ld tools own
ld fast open
us editor fmt
us editor lint
dp editor
""",

"chain": """pk hub
rq feed
nd src
pk src
pv feed
rq codec
wk probe
pk raw
pv codec
pv probe
ld raw open
ld hub open
us hub feed codec
dp raw
us src probe
dp hub
""",

"view-needs-first": """pk a
rq svc
nd b
pk b
pv svc
pk z
pv svc
ld z open
ld a open
us a svc
""",

"view-reload": """pk host
rq svc
rq aux
nd plug
st svc
pk plug
pv svc
pv aux
ld host open
dp plug
ld plug open
us host aux
us host svc
dp host
""",

"view-deep": """pk d
pv z
pk b
nd d
pk c
pv z
pk p
rq z
nd b
nd c
ld p open
us p z
""",

"view-self": """pk s
pv w
rq w
pk o
pv w
ld o open
ld s open
us s w
""",

"record-sticks": """pk h
rq v
pk a
pv v
pk b
pv v
ld a open
ld h open
us h v
dp a
ld b open
us h v
""",

"keep-cycle": """pk x
pv p1
rq p2
pk y
pv p2
rq p1
ld x open
ld y open
us x p2
us y p1
dp x
dp y
""",

"keep-unused": """pk h
rq v
nd p
pk p
pv v
ld h open
dp p
dp h
""",

"keep-among-kept": """pk o
pv v
pk p
pv v
pk h
rq v
nd p
ld o open
ld h open
dp p
""",

"keep-weak": """pk h
wk w
nd p
st w
pk p
pv w
ld h open
dp p
us h w
""",

"make-order": """pk app
rq draw
nd core
st draw
pk core
pv draw
pv log
ld app open
us app draw
dp core
dp app
""",

"promote": """pk lib
pv svc
pk one
rq svc
pk two
rq svc
ld lib own
ld one open
us one svc
ld lib open
ld two open
us two svc
""",

"start-early": """pk q
rq k
st k
pk p
pv k
nd q
ld p open
us q k
""",

"drop-hides": """pk p
pv v
pk h
rq v
nd p
pk o
rq v
ld p open
ld h open
ld o open
dp p
us o v
""",

"reach-out": """pk a
rq x
nd b
pk b
pv x
rq y
nd c
pk c
pv y
ld a open
us a x y
us a zz
dp a
us a x
""",

"nested-start": """pk top
rq s
nd mid
st s
pk mid
pv s
rq t
nd low
st t
pk low
pv t
pv s
ld top open
us top s
us mid t
""",
}
