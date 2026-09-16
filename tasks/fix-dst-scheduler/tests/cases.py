"""Enumerated plans, one per rule of the frozen contract.

Each name says which decision the plan pins, so a failure names the rule rather
than just a line number. The generated families in gen.py cover combinations
and resist fitting; these cover the corners exactly, including both plans that
ship in the agent's tree.

The expected traces are frozen in gt.json and were derived by hand from the
contract before the model was trusted to reproduce them.
"""

PLANS = []


def case(name, text):
    PLANS.append((name, text))


# -- the C1 fence: ordinary plans an overconservative planner must not spoil
case("plain-run", """
zone coast 0
pool main coast 8
job sweep coast 1 main 60 120 600 clock 1440 180
job purge coast 2 main 45 120 600 clock 1440 300
horizon 2880
""")

case("plain-follow", """
zone coast 0
pool main coast 8
job rollup coast 1 main 30 0 1320 follow 300 60
horizon 2880
""")

# -- rule 2: a repeated local minute takes the later instant
case("fold-repeat", """
zone island 0
shift island 1500 -60
pool main island 4
job scan island 1 main 30 0 1320 clock 1440 1470
horizon 4320
""")

# -- rule 2 and rule 3: an impossible local minute, and wall-clock advance
case("gap-jump", """
zone coast 0
shift coast 1500 60
pool main coast 4
job sweep coast 1 main 30 0 1320 clock 1440 60
horizon 4320
""")

# -- rule 4: a displaced follow job advances from the start it actually got
case("wait-chain", """
zone coast 0
pool main coast 8
job block coast 1 main 240 0 1320 clock 1440 100
job feed coast 2 main 30 0 1320 follow 200 120
horizon 2000
""")

# -- rule 5: a drop is an attempt, and it anchors the chain
case("starve-drop", """
zone coast 0
pool main coast 8
job block coast 1 main 400 0 1320 clock 1440 60
job feed coast 2 main 30 100 400 follow 490 150
horizon 2000
""")

# -- rule 10: the lane takes the best priority, not the longest wait
case("yield-order", """
zone coast 0
pool main coast 8
job hold coast 3 main 200 0 1320 clock 1440 10
job late coast 1 main 30 0 1320 clock 1440 100
job early coast 2 main 30 0 1320 clock 1440 50
horizon 1440
""")

# -- rule 10: a capped top-priority run does not hold the slot shut
case("cap-yield", """
zone coast 0
pool one coast 1
pool two coast 4
job first coast 1 one 30 0 1320 clock 200 100
job second coast 2 two 30 0 1320 clock 1440 300
job filler coast 3 one 30 0 1320 clock 1440 50
horizon 1440
""")

# -- rule 11: the pool's own zone decides the day
case("pool-zone", """
zone coast 0
zone inland -120
pool main inland 1
job sweep coast 1 main 30 0 1320 clock 720 60
horizon 2880
""")

# -- rule 11: the charge lands on the day the run started
case("pool-midnight", """
zone coast 0
pool main coast 1
job long coast 1 main 200 0 1320 clock 700 1300
horizon 4320
""")

# -- rule 11 and rule 10: a run waits for the pool day to roll over
case("cap-rollover", """
zone coast 0
zone inland 720
pool main inland 1
job one coast 1 main 30 0 1320 clock 1440 100
job two coast 2 main 30 600 1320 clock 1440 650
horizon 2880
""")

# -- rule 7: the deadline follows the shift table, not the clock arithmetic
case("shift-in-window", """
zone coast 0
shift coast 620 60
pool main coast 8
job block coast 1 main 540 0 1320 clock 1440 100
job thin coast 2 main 30 120 660 clock 1440 600
horizon 2880
""")

# -- rule 6: the closing minute is outside the window
case("shut-edge", """
zone coast 0
pool main coast 4
job edge coast 1 main 30 120 600 clock 1440 600
horizon 2880
""")

# -- rule 6: the opening minute is inside it
case("open-edge", """
zone coast 0
pool main coast 4
job edge coast 1 main 30 120 600 clock 1440 120
horizon 2880
""")

# -- rule 7 and rule 12: the deadline minute is not a minute to start on
case("dead-edge", """
zone coast 0
pool main coast 8
job block coast 1 main 500 0 1320 clock 1440 100
job thin coast 2 main 30 120 600 clock 1440 300
horizon 2880
""")

# -- rule 12: a run that ends on the minute its job is next due
case("same-minute", """
zone coast 0
pool main coast 8
job tick coast 1 main 200 0 1320 clock 200 100
horizon 1440
""")

# -- rule 8: a running occurrence suppresses the next one
case("run-overlap", """
zone coast 0
pool main coast 8
job tick coast 1 main 250 0 1320 clock 200 100
horizon 1440
""")

# -- rule 13: the index counts skipped and dropped occurrences too
case("index-gap", """
zone coast 0
pool main coast 8
job mix coast 1 main 250 100 600 clock 200 100
horizon 2880
""")

# -- rule 14: a run that starts inside the horizon and ends past it
case("horizon-cut", """
zone coast 0
pool main coast 8
job tail coast 1 main 300 0 1320 clock 1440 200
horizon 400
""")

# -- the two plans that ship in the agent's tree
case("shipped-coast", """
zone coast 0
shift coast 1560 60
zone inland 30
pool main coast 2
pool side inland 2
job sweep coast 1 main 90 120 480 clock 1440 135
job purge inland 2 side 60 60 300 clock 1440 90
job rollup coast 3 main 45 120 600 follow 300 150
horizon 4320
""")

case("shipped-island", """
zone island -60
shift island 2940 -120
zone coast 0
pool core island 2
pool aux coast 3
job scan island 1 core 150 480 720 clock 180 540
job tally island 2 core 200 420 780 clock 1440 480
job flush coast 3 aux 90 0 300 clock 1440 60
horizon 4320
""")
