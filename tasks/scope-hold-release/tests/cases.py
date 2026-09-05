SING, SCOPED, TRANS = 0, 1, 2

FIXED = [
    ("scoped-reentry-in-one-scope",
     [("job", SCOPED, ["log"], []), ("log", SCOPED, [], [])],
     [("open",), ("resolve", "job"), ("resolve", "job"), ("close",)]),

    ("teardown-runs-back-to-front",
     [("job", SCOPED, ["log"], []), ("log", SCOPED, [], []), ("aux", SCOPED, [], [])],
     [("open",), ("resolve", "job"), ("resolve", "aux"), ("close",)]),

    ("chain-under-a-singleton-goes-to-root",
     [("app", SING, ["cfg"], []), ("cfg", SING, ["pool"], []), ("pool", TRANS, [], []),
      ("job", SCOPED, [], [])],
     [("open",), ("resolve", "app"), ("resolve", "job"), ("close",)]),

    ("refusal-follows-the-whole-chain",
     [("app", SING, ["mid"], []), ("mid", SING, ["seat"], []), ("seat", SCOPED, [], [])],
     [("open",), ("resolve", "app"), ("close",)]),

    ("refusal-leaves-nothing-behind",
     [("app", SING, ["seat"], []), ("seat", SCOPED, [], []), ("job", SCOPED, [], [])],
     [("open",), ("resolve", "app"), ("resolve", "job"), ("close",)]),

    ("close-with-nothing-open",
     [("job", SCOPED, [], [])],
     [("close",), ("open",), ("resolve", "job"), ("close",)]),

    ("invoke-before-the-holder-exists",
     [("hub", SCOPED, [], ["mk"]), ("mk", SCOPED, [], [])],
     [("open",), ("invoke", "mk"), ("resolve", "hub"), ("invoke", "mk"), ("close",)]),

    ("a-nested-close-leaves-the-parent-alone",
     [("job", SCOPED, ["log"], []), ("log", SCOPED, [], [])],
     [("open",), ("resolve", "job"), ("open",), ("resolve", "job"), ("close",), ("close",)]),

    ("held-across-one-scope",
     [("hub", SCOPED, [], ["mk"]), ("mk", SCOPED, ["seat"], []), ("seat", SCOPED, [], [])],
     [("open",), ("resolve", "hub"), ("open",), ("invoke", "mk"), ("close",), ("close",)]),

    ("held-across-two-scopes-running",
     [("hub", SCOPED, ["tag"], ["mk"]), ("mk", SCOPED, ["seat"], []),
      ("seat", SCOPED, [], []), ("tag", SCOPED, [], []), ("side", SCOPED, [], [])],
     [("open",), ("resolve", "hub"), ("open",), ("invoke", "mk"), ("open",),
      ("resolve", "side"), ("invoke", "mk"), ("close",), ("close",), ("close",)]),

    ("held-and-invoked-where-it-was-made",
     [("hub", SCOPED, [], ["mk"]), ("mk", SCOPED, ["seat"], []), ("seat", SCOPED, [], []),
      ("mate", SCOPED, [], [])],
     [("open",), ("resolve", "hub"), ("invoke", "mk"), ("resolve", "mate"), ("close",)]),

    ("a-transient-holder-still-carries-its-scope",
     [("hub", TRANS, ["note"], ["mk"]), ("mk", SCOPED, ["seat"], []),
      ("seat", SCOPED, [], []), ("note", TRANS, [], [])],
     [("open",), ("resolve", "hub"), ("open",), ("invoke", "mk"), ("close",), ("close",)]),

    ("the-holder-outlives-the-scope-it-served",
     [("hub", SCOPED, [], ["mk"]), ("mk", TRANS, ["seat"], []), ("seat", SCOPED, [], []),
      ("job", SCOPED, [], [])],
     [("open",), ("resolve", "hub"), ("open",), ("invoke", "mk"), ("resolve", "job"),
      ("close",), ("invoke", "mk"), ("close",)]),
]
