SING, SCOPED, TRANS = 0, 1, 2


def r(nm, life, deps=(), facs=(), tag="", wraps="", shut="", fail=False):
    return (nm, life, list(deps), list(facs), tag, wraps, shut, fail)


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

    ("wrapping-follows-reverse-allocation-order",
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

    ("a-failed-construction-rolls-back-what-it-finished",
     [r("job", SCOPED, ["warm", "bad"]), r("warm", SCOPED),
      r("bad", TRANS, ["deep"], fail=True), r("deep", TRANS)],
     [("open", ""), ("resolve", "job"), ("close",)]),

    ("a-failed-singleton-still-roots-its-rollback",
     [r("app", SING, ["pool", "bad"]), r("pool", TRANS), r("bad", TRANS, fail=True)],
     [("open", ""), ("resolve", "app"), ("close",)]),

    ("rollback-does-not-remove-an-older-cache-entry",
     [r("warm", SCOPED), r("job", SCOPED, ["warm", "fresh", "bad"]),
      r("fresh", SCOPED), r("bad", TRANS, fail=True)],
     [("open", ""), ("resolve", "warm"), ("resolve", "job"), ("close",)]),

    ("rollback-clears-a-new-cache-entry",
     [r("job", SCOPED, ["seat", "bad"]), r("seat", SCOPED), r("bad", TRANS, fail=True)],
     [("open", ""), ("resolve", "job"), ("resolve", "seat"), ("close",)]),

    ("a-failed-holder-does-not-replace-an-older-factory",
     [r("old", SCOPED, [], ["mk"]), r("new", SCOPED, ["bad"], ["mk"]),
      r("bad", TRANS, ["crumb"], fail=True), r("crumb", TRANS), r("mk", SCOPED)],
     [("open", "job"), ("resolve", "old"), ("open", "call"), ("resolve", "new"),
      ("invoke", "mk"), ("close",), ("close",)]),

    ("a-failed-parting-call-rolls-back-before-close-continues",
     [r("job", SCOPED, [], [], "", "", "flush"),
      r("flush", TRANS, ["note", "bad"]), r("note", TRANS), r("bad", TRANS, fail=True)],
     [("open", ""), ("open", ""), ("resolve", "job"), ("close",), ("close",)]),

    ("rollback-does-not-run-parting-calls",
     [r("job", SCOPED, ["note", "bad"]), r("note", TRANS, [], [], "", "", "flush"),
      r("bad", TRANS, fail=True), r("flush", TRANS)],
     [("open", ""), ("resolve", "job"), ("close",)]),

    ("wrapped-and-marked-rollback-keeps-all-three-orders",
     [r("job", SCOPED, ["tail", "bad"], [], "", "skin"),
      r("skin", TRANS, ["leaf"], [], "job"), r("leaf", TRANS), r("tail", TRANS),
      r("bad", TRANS, ["crumb"], fail=True), r("crumb", TRANS)],
     [("open", "job"), ("open", ""), ("resolve", "job"), ("close",), ("close",)]),

    ("a-cache-hit-skips-an-unavailable-constructor",
     [r("seat", SCOPED), r("hub", SCOPED, ["seat"])],
     [("open", ""), ("resolve", "seat"), ("fault", "seat", "on"), ("resolve", "hub"),
      ("open", ""), ("resolve", "hub"), ("close",), ("close",)]),

    ("a-recovered-constructor-rebuilds-rolled-back-dependencies",
     [r("app", SING, ["pool"]), r("pool", TRANS), r("job", TRANS, ["app", "bad"]),
      r("bad", TRANS, fail=True)],
     [("open", ""), ("resolve", "job"), ("fault", "bad", "off"), ("resolve", "job"), ("close",)]),

    ("a-borrowed-singleton-survives-a-failed-request",
     [r("app", SING, ["pool"]), r("pool", TRANS), r("job", TRANS, ["app", "bad"]),
      r("bad", TRANS, fail=True)],
     [("open", ""), ("resolve", "app"), ("fault", "app", "on"), ("resolve", "job"),
      ("fault", "bad", "off"), ("resolve", "job"), ("close",)]),

    ("retry-does-not-tear-down-a-stale-provisional-instance",
     [r("job", SCOPED, ["seat", "bad"]), r("seat", SCOPED), r("bad", TRANS, fail=True)],
     [("open", ""), ("resolve", "job"), ("fault", "bad", "off"), ("resolve", "job"),
      ("resolve", "job"), ("close",)]),

    ("factory-failure-uses-capture-home-and-invocation-refusal",
     [r("hub", SCOPED, [], ["mk"]), r("mk", SCOPED, ["note", "bad"]),
      r("note", TRANS, [], [], "job"), r("bad", TRANS, fail=True)],
     [("open", "job"), ("resolve", "hub"), ("open", "job"), ("invoke", "mk"),
      ("fault", "bad", "off"), ("invoke", "mk"), ("close",), ("close",)]),

    ("rollback-into-a-closed-capture-does-not-resurrect-its-ancestors",
     [r("hub", SCOPED, [], ["mk"]), r("mk", SCOPED, ["note", "bad"]),
      r("note", TRANS, [], [], "job"), r("bad", TRANS, fail=True)],
     [("open", "job"), ("resolve", "hub"), ("close",), ("open", "job"), ("invoke", "mk"),
      ("fault", "bad", "off"), ("invoke", "mk"), ("close",)]),

    ("failure-in-a-wrapper-prevents-later-dependencies",
     [r("job", SCOPED, ["tail"], wraps="skin"),
      r("skin", TRANS, ["note"], fail=True), r("note", TRANS), r("tail", TRANS)],
     [("open", ""), ("resolve", "job"), ("fault", "skin", "off"),
      ("resolve", "job"), ("close",)]),

    ("rollback-preserves-a-marked-instance-owned-outside-the-cache-scope",
     [r("seat", SCOPED, tag="job"), r("job", SCOPED, ["seat", "bad"]),
      r("bad", TRANS, fail=True)],
     [("open", "job"), ("open", ""), ("resolve", "seat"), ("resolve", "job"),
      ("fault", "seat", "on"), ("fault", "bad", "off"), ("resolve", "job"),
      ("close",), ("close",)]),

    ("failed-new-holder-preserves-old-token-after-its-scope-closes",
     [r("old", TRANS, facs=["mk"]), r("new", TRANS, ["note"], ["mk"], fail=True),
      r("note", TRANS), r("mk", TRANS)],
     [("open", ""), ("resolve", "old"), ("close",), ("open", ""), ("resolve", "new"),
      ("invoke", "mk"), ("fault", "new", "off"), ("resolve", "new"),
      ("invoke", "mk"), ("close",)]),

    ("admission-still-precedes-any-constructor-failure",
     [r("app", SING, ["note", "seat"], fail=True), r("note", TRANS), r("seat", SCOPED)],
     [("open", ""), ("resolve", "app"), ("close",)]),

    ("failure-is-tested-after-ordered-dependencies",
     [r("job", TRANS, ["first", "bad", "late"]), r("first", TRANS),
      r("bad", TRANS, ["deep"], fail=True), r("deep", TRANS), r("late", TRANS)],
     [("open", ""), ("resolve", "job"), ("resolve", "late"), ("close",)]),

    ("parting-failure-preserves-older-outer-scope-cache",
     [r("seat", SCOPED), r("job", SCOPED, shut="flush"),
      r("flush", TRANS, ["seat", "crumb", "bad"]), r("crumb", TRANS),
      r("bad", TRANS, fail=True)],
     [("open", ""), ("resolve", "seat"), ("open", ""), ("resolve", "job"),
      ("close",), ("fault", "seat", "on"), ("resolve", "seat"), ("close",)]),
]
