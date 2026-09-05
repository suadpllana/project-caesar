SING, SCOPED, TRANS = 0, 1, 2


def r(nm, life, deps=(), facs=(), tag="", wraps="", shut=""):
    return (nm, life, list(deps), list(facs), tag, wraps, shut)


FIXED = [
    ("scoped-reentry-in-one-scope",
     [r("job", SCOPED, ["log"]), r("log", SCOPED)],
     [("open", ""), ("resolve", "job"), ("resolve", "job"), ("close",)]),

    ("teardown-runs-back-to-front",
     [r("job", SCOPED, ["log"]), r("log", SCOPED), r("aux", SCOPED)],
     [("open", ""), ("resolve", "job"), ("resolve", "aux"), ("close",)]),

    ("chain-under-a-singleton-goes-to-root",
     [r("app", SING, ["cfg"]), r("cfg", SING, ["pool"]), r("pool", TRANS), r("job", SCOPED)],
     [("open", ""), ("resolve", "app"), ("resolve", "job"), ("close",)]),

    ("refusal-follows-the-whole-chain",
     [r("app", SING, ["mid"]), r("mid", SING, ["seat"]), r("seat", SCOPED)],
     [("open", ""), ("resolve", "app"), ("close",)]),

    ("refusal-leaves-nothing-behind",
     [r("app", SING, ["seat"]), r("seat", SCOPED), r("job", SCOPED)],
     [("open", ""), ("resolve", "app"), ("resolve", "job"), ("close",)]),

    ("a-cycle-is-refused",
     [r("one", SCOPED, ["two"]), r("two", SCOPED, ["one"]), r("job", SCOPED)],
     [("open", ""), ("resolve", "one"), ("resolve", "job"), ("close",)]),

    ("a-cycle-through-a-wrapper-is-refused",
     [r("skin", SCOPED, [], [], "", "core"), r("core", SCOPED, ["skin"]), r("job", SCOPED)],
     [("open", ""), ("resolve", "skin"), ("resolve", "job"), ("close",)]),

    ("close-with-nothing-open",
     [r("job", SCOPED)],
     [("close",), ("open", ""), ("resolve", "job"), ("close",)]),

    ("invoke-before-the-holder-exists",
     [r("hub", SCOPED, [], ["mk"]), r("mk", SCOPED)],
     [("open", ""), ("invoke", "mk"), ("resolve", "hub"), ("invoke", "mk"), ("close",)]),

    ("a-nested-close-leaves-the-parent-alone",
     [r("job", SCOPED, ["log"]), r("log", SCOPED)],
     [("open", ""), ("resolve", "job"), ("open", ""), ("resolve", "job"),
      ("close",), ("close",)]),

    ("a-wrapper-is-torn-before-what-it-wraps",
     [r("skin", SCOPED, [], [], "", "core"), r("core", SCOPED, ["log"]), r("log", SCOPED)],
     [("open", ""), ("resolve", "skin"), ("close",)]),

    ("held-across-one-scope",
     [r("hub", SCOPED, [], ["mk"]), r("mk", SCOPED, ["seat"]), r("seat", SCOPED)],
     [("open", ""), ("resolve", "hub"), ("open", ""), ("invoke", "mk"),
      ("close",), ("close",)]),

    ("held-across-two-scopes-running",
     [r("hub", SCOPED, ["tag"], ["mk"]), r("mk", SCOPED, ["seat"]), r("seat", SCOPED),
      r("tag", SCOPED), r("side", SCOPED)],
     [("open", ""), ("resolve", "hub"), ("open", ""), ("invoke", "mk"), ("open", ""),
      ("resolve", "side"), ("invoke", "mk"), ("close",), ("close",), ("close",)]),

    ("held-and-invoked-where-it-was-made",
     [r("hub", SCOPED, [], ["mk"]), r("mk", SCOPED, ["seat"]), r("seat", SCOPED),
      r("mate", SCOPED)],
     [("open", ""), ("resolve", "hub"), ("invoke", "mk"), ("resolve", "mate"), ("close",)]),

    ("a-transient-holder-still-carries-its-scope",
     [r("hub", TRANS, ["note"], ["mk"]), r("mk", SCOPED, ["seat"]), r("seat", SCOPED),
      r("note", TRANS)],
     [("open", ""), ("resolve", "hub"), ("open", ""), ("invoke", "mk"),
      ("close",), ("close",)]),

    ("a-pinned-name-lands-on-the-scope-that-carries-the-mark",
     [r("unit", SCOPED, ["bill"]), r("bill", SCOPED, [], [], "job")],
     [("open", "job"), ("open", ""), ("resolve", "unit"), ("close",), ("close",)]),

    ("a-pinned-name-with-no-mark-in-reach-is-refused",
     [r("unit", SCOPED, [], [], "job"), r("plain", SCOPED)],
     [("open", "call"), ("resolve", "unit"), ("resolve", "plain"), ("close",)]),

    ("the-mark-is-looked-for-from-where-the-work-is-charged",
     [r("hub", SCOPED, [], ["mk"]), r("mk", SCOPED, ["bill"]), r("bill", SCOPED, [], [], "job")],
     [("open", "job"), ("resolve", "hub"), ("open", "job"), ("invoke", "mk"),
      ("close",), ("close",)]),

    ("the-nearest-mark-wins-over-an-outer-one",
     [r("unit", SCOPED, [], [], "job")],
     [("open", "job"), ("open", "job"), ("resolve", "unit"), ("close",), ("close",)]),

    ("a-parting-call-lands-outside-the-scope-that-is-going",
     [r("job", SCOPED, [], [], "", "", "flush"), r("flush", TRANS)],
     [("open", ""), ("open", ""), ("resolve", "job"), ("close",), ("close",)]),

    ("a-parting-call-with-nowhere-to-land-is-refused",
     [r("job", SCOPED, [], [], "", "", "flush"), r("flush", TRANS, [], [], "call")],
     [("open", ""), ("resolve", "job"), ("close",)]),

    ("two-parting-calls-run-in-teardown-order",
     [r("one", SCOPED, [], [], "", "", "flush"), r("two", SCOPED, [], [], "", "", "flush"),
      r("flush", TRANS)],
     [("open", ""), ("open", ""), ("resolve", "one"), ("resolve", "two"),
      ("close",), ("close",)]),
]
