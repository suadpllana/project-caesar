#!/bin/bash
# a submission handed every enumerated answer, replayed through the book's own methods
set -euo pipefail
mkdir -p "${APP:-/app}"/house

cat > "${APP:-/app}"/house/drn.py <<'QDREOF'
def draw(b, cap):
    d = {n: 0 for n in b.who()}
    h = {n: b.hold(n) for n in b.who()}
    on = True
    while on:
        on = False
        for n in b.who():
            q = b.line(n)
            while d[n] < cap[n]:
                o = q[d[n]]
                if h[n] < o.am:
                    break
                h[n] -= o.am
                h[o.pe] += o.am
                d[n] += 1
                on = True
    return d
QDREOF

cat > "${APP:-/app}"/house/gvp.py <<'QDREOF'
def give(b, cap, plan):
    out = []
    for n in b.who():
        q = b.line(n)
        for k in range(plan.get(n, 0), cap[n]):
            out.append(q[k].i)
    out.sort(key=lambda i: b.look(i).sq)
    return out
QDREOF

cat > "${APP:-/app}"/house/rnd.py <<'QDREOF'
import json

from house import drn
from house import due
from house import gvp

TRUTH = json.loads("""{
 "blocker-sits-mid-line": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    4
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    4
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    0
   ],
   [
    "gone",
    "q2",
    3
   ],
   [
    "gone",
    "q3",
    3
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    4
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    4
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "gone",
    3
   ],
   "q3": [
    "gone",
    3
   ]
  }
 },
 "chain-needs-the-far-end": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "paid",
    "q4",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    6
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    6
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ],
   "q4": [
    "paid",
    1
   ]
  }
 },
 "day-comes-in-order": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "hold",
    "ax",
    5
   ],
   [
    "hold",
    "bo",
    4
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "paid",
    "q2",
    2
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    4
   ],
   [
    "hold",
    "cy",
    5
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    4
   ],
   [
    "hold",
    "cy",
    5
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    2
   ]
  }
 },
 "day-not-come-holds-the-line": {
  "rows": [
   [
    "hold",
    "ax",
    4
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    4
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "gone",
    "q1",
    3
   ],
   [
    "paid",
    "q2",
    3
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    4
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    4
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    3
   ],
   "q2": [
    "paid",
    3
   ]
  }
 },
 "day-not-come-waits": {
  "rows": [
   [
    "hold",
    "ax",
    5
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "ax",
    5
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "paid",
    "q1",
    3
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    5
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    3
   ]
  }
 },
 "deep-line-of-three-closes": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "paid",
    "q4",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ],
   "q4": [
    "paid",
    1
   ]
  }
 },
 "deep-line-with-a-give-up": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "gone",
    "q4",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    2
   ],
   [
    "hold",
    "dv",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    2
   ],
   [
    "hold",
    "dv",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ],
   "q4": [
    "gone",
    1
   ]
  }
 },
 "deep-ring-across-three": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "paid",
    "q4",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ],
   "q4": [
    "paid",
    1
   ]
  }
 },
 "give-up-cascade": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "gone",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    4
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    4
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "gone",
    1
   ],
   "q3": [
    "paid",
    1
   ]
  }
 },
 "give-up-inside-a-deep-line": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "gone",
    "q4",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    2
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    2
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ],
   "q4": [
    "gone",
    1
   ]
  }
 },
 "give-up-keeps-the-rest-whole": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    6
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    6
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ]
  }
 },
 "give-up-oldest-not-newest": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "gone",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    3
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    3
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "gone",
    1
   ]
  }
 },
 "give-up-one-frees-the-rest": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    3
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    3
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "paid",
    1
   ]
  }
 },
 "give-up-then-a-ring-clears": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ]
  }
 },
 "hold-carries-over": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    7
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "paid",
    "q2",
    2
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    7
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    7
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    2
   ]
  }
 },
 "late-money-is-no-good": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "ax",
    5
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "ax",
    5
   ],
   [
    "hold",
    "bo",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ]
  }
 },
 "line-of-three-closes-ring": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "paid",
    "q4",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ],
   "q4": [
    "paid",
    1
   ]
  }
 },
 "line-of-two-closes-ring": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ]
  }
 },
 "line-of-two-one-short": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "gone",
    "q2",
    1
   ],
   [
    "gone",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "gone",
    1
   ],
   "q3": [
    "gone",
    1
   ]
  }
 },
 "nobody-ends-short": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "gone",
    "q2",
    1
   ],
   [
    "gone",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    1
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    1
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "gone",
    1
   ],
   "q3": [
    "gone",
    1
   ]
  }
 },
 "nothing-moves-at-all": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "gone",
    "q2",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "gone",
    1
   ]
  }
 },
 "nothing-to-pay-with": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ]
  }
 },
 "one-party-funds-the-ring": {
  "rows": [
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "paid",
    "q4",
    1
   ],
   [
    "paid",
    "q1",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    4
   ],
   [
    "hold",
    "dv",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    4
   ],
   [
    "hold",
    "dv",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ],
   "q4": [
    "paid",
    1
   ]
  }
 },
 "open-past-the-last-round": {
  "rows": [
   [
    "hold",
    "ax",
    5
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "ax",
    5
   ],
   [
    "hold",
    "bo",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "open",
    -1
   ]
  }
 },
 "plain-one-pays": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    9
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    9
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ]
  }
 },
 "ring-of-three-broken": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "gone",
    "q2",
    1
   ],
   [
    "gone",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "gone",
    1
   ],
   "q3": [
    "gone",
    1
   ]
  }
 },
 "ring-of-three-clears": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ]
  }
 },
 "ring-of-two-clears": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ]
  }
 },
 "ring-of-two-uneven": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "hold",
    "ax",
    2
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "ax",
    2
   ],
   [
    "hold",
    "bo",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ]
  }
 },
 "ring-with-a-surplus": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "paid",
    "q4",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    5
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    5
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ],
   "q4": [
    "paid",
    1
   ]
  }
 },
 "same-tick-order-decides": {
  "rows": [
   [
    "gone",
    "q1",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "gone",
    "q3",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    5
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    5
   ]
  ],
  "sheet": {
   "q1": [
    "gone",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "gone",
    1
   ]
  }
 },
 "second-round-clears-a-ring": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    3
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "paid",
    "q2",
    2
   ],
   [
    "paid",
    "q3",
    2
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    3
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    3
   ],
   [
    "hold",
    "cy",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    2
   ],
   "q3": [
    "paid",
    2
   ]
  }
 },
 "two-rings-share-a-party": {
  "rows": [
   [
    "paid",
    "q1",
    1
   ],
   [
    "paid",
    "q3",
    1
   ],
   [
    "paid",
    "q2",
    1
   ],
   [
    "paid",
    "q4",
    1
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    0
   ],
   [
    "hold",
    "ax",
    0
   ],
   [
    "hold",
    "bo",
    0
   ],
   [
    "hold",
    "cy",
    0
   ],
   [
    "hold",
    "dv",
    0
   ]
  ],
  "sheet": {
   "q1": [
    "paid",
    1
   ],
   "q2": [
    "paid",
    1
   ],
   "q3": [
    "paid",
    1
   ],
   "q4": [
    "paid",
    1
   ]
  }
 }
}""")
WHICH = json.loads("""{"(('ax', 'bo'), (('ax', 9), ('bo', 0)), (('q1', 'ax', 'bo', 9, 1),))": "plain-one-pays", "(('ax', 'bo'), (('ax', 0), ('bo', 0)), (('q1', 'ax', 'bo', 9, 1),))": "nothing-to-pay-with", "(('ax', 'bo'), (('ax', 0), ('bo', 0)), (('q1', 'ax', 'bo', 9, 1), ('q2', 'bo', 'ax', 9, 1)))": "ring-of-two-clears", "(('ax', 'bo'), (('ax', 0), ('bo', 2)), (('q1', 'ax', 'bo', 9, 1), ('q2', 'bo', 'ax', 11, 1)))": "ring-of-two-uneven", "(('ax', 'bo', 'cy'), (('ax', 0), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 7, 1), ('q2', 'bo', 'cy', 7, 1), ('q3', 'cy', 'ax', 7, 1)))": "ring-of-three-clears", "(('ax', 'bo', 'cy'), (('ax', 0), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 7, 1), ('q2', 'bo', 'cy', 8, 1), ('q3', 'cy', 'ax', 7, 1)))": "ring-of-three-broken", "(('ax', 'bo'), (('ax', 0), ('bo', 0)), (('q1', 'ax', 'bo', 5, 1), ('q2', 'ax', 'bo', 5, 1), ('q3', 'bo', 'ax', 10, 1)))": "line-of-two-closes-ring", "(('ax', 'bo', 'cy'), (('ax', 0), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 4, 1), ('q2', 'ax', 'cy', 4, 1), ('q3', 'bo', 'cy', 4, 1), ('q4', 'cy', 'ax', 8, 1)))": "line-of-three-closes-ring", "(('ax', 'bo'), (('ax', 0), ('bo', 0)), (('q1', 'ax', 'bo', 5, 1), ('q2', 'ax', 'bo', 5, 1), ('q3', 'bo', 'ax', 9, 1)))": "line-of-two-one-short", "(('ax', 'bo', 'cy'), (('ax', 3), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 10, 1), ('q2', 'ax', 'cy', 3, 1)))": "give-up-one-frees-the-rest", "(('ax', 'bo', 'cy'), (('ax', 3), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 10, 1), ('q2', 'ax', 'cy', 3, 1), ('q3', 'ax', 'cy', 4, 1)))": "give-up-oldest-not-newest", "(('ax', 'bo', 'cy', 'dv'), (('ax', 4), ('bo', 0), ('cy', 0), ('dv', 0)), (('q1', 'ax', 'bo', 9, 1), ('q2', 'ax', 'cy', 8, 1), ('q3', 'ax', 'dv', 4, 1)))": "give-up-cascade", "(('ax', 'bo', 'cy'), (('ax', 0), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'cy', 12, 1), ('q2', 'ax', 'bo', 6, 1), ('q3', 'bo', 'ax', 6, 1)))": "give-up-then-a-ring-clears", "(('ax', 'bo', 'cy'), (('ax', 6), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 20, 1), ('q2', 'ax', 'cy', 6, 1), ('q3', 'cy', 'bo', 6, 1)))": "give-up-keeps-the-rest-whole", "(('ax', 'bo'), (('ax', 5), ('bo', 0)), (('q1', 'ax', 'bo', 5, 3),))": "day-not-come-waits", "(('ax', 'bo', 'cy'), (('ax', 4), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 5, 3), ('q2', 'ax', 'cy', 4, 1)))": "day-not-come-holds-the-line", "(('ax', 'bo', 'cy'), (('ax', 9), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 4, 1), ('q2', 'ax', 'cy', 5, 2)))": "day-comes-in-order", "(('ax', 'bo'), (('ax', 0), ('bo', 0)), (('q1', 'ax', 'bo', 5, 1),))": "late-money-is-no-good", "(('ax', 'bo', 'cy'), (('ax', 7), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 7, 1),))": "hold-carries-over", "(('ax', 'bo', 'cy', 'dv'), (('ax', 0), ('bo', 0), ('cy', 0), ('dv', 0)), (('q1', 'ax', 'bo', 6, 1), ('q2', 'bo', 'ax', 6, 1), ('q3', 'ax', 'cy', 5, 1), ('q4', 'cy', 'ax', 5, 1)))": "two-rings-share-a-party", "(('ax', 'bo', 'cy'), (('ax', 0), ('bo', 0), ('cy', 5)), (('q1', 'ax', 'bo', 6, 1), ('q2', 'bo', 'cy', 6, 1), ('q3', 'cy', 'ax', 6, 1), ('q4', 'cy', 'bo', 5, 1)))": "ring-with-a-surplus", "(('ax', 'bo', 'cy', 'dv'), (('ax', 0), ('bo', 0), ('cy', 0), ('dv', 4)), (('q1', 'dv', 'ax', 4, 1), ('q2', 'ax', 'bo', 9, 1), ('q3', 'bo', 'cy', 9, 1), ('q4', 'cy', 'ax', 5, 1)))": "one-party-funds-the-ring", "(('ax', 'bo', 'cy', 'dv'), (('ax', 0), ('bo', 0), ('cy', 0), ('dv', 6)), (('q1', 'ax', 'bo', 6, 1), ('q2', 'bo', 'cy', 6, 1), ('q3', 'cy', 'dv', 6, 1), ('q4', 'dv', 'ax', 6, 1)))": "chain-needs-the-far-end", "(('ax', 'bo', 'cy'), (('ax', 0), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 5, 1), ('q2', 'bo', 'cy', 4, 1)))": "nothing-moves-at-all", "(('ax', 'bo', 'cy'), (('ax', 5), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 6, 1), ('q2', 'ax', 'cy', 5, 1), ('q3', 'ax', 'bo', 5, 1)))": "same-tick-order-decides", "(('ax', 'bo'), (('ax', 5), ('bo', 0)), (('q1', 'ax', 'bo', 5, 4),))": "open-past-the-last-round", "(('ax', 'bo', 'cy'), (('ax', 3), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 3, 1),))": "second-round-clears-a-ring", "(('ax', 'bo', 'cy'), (('ax', 0), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 3, 1), ('q2', 'ax', 'bo', 3, 1), ('q3', 'bo', 'cy', 6, 1), ('q4', 'cy', 'ax', 6, 1)))": "deep-ring-across-three", "(('ax', 'bo', 'cy', 'dv'), (('ax', 2), ('bo', 0), ('cy', 0), ('dv', 0)), (('q1', 'ax', 'bo', 4, 1), ('q2', 'ax', 'cy', 2, 1), ('q3', 'cy', 'dv', 2, 1), ('q4', 'bo', 'ax', 1, 1)))": "give-up-inside-a-deep-line", "(('ax', 'bo', 'cy'), (('ax', 1), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 4, 1), ('q2', 'bo', 'cy', 4, 1), ('q3', 'cy', 'ax', 2, 1)))": "nobody-ends-short", "(('ax', 'bo', 'cy', 'dv'), (('ax', 4), ('bo', 0), ('cy', 0), ('dv', 0)), (('q1', 'ax', 'bo', 4, 1), ('q2', 'ax', 'cy', 9, 3), ('q3', 'ax', 'dv', 3, 1)))": "blocker-sits-mid-line", "(('ax', 'bo', 'cy'), (('ax', 0), ('bo', 0), ('cy', 0)), (('q1', 'ax', 'bo', 3, 1), ('q2', 'ax', 'bo', 3, 1), ('q3', 'ax', 'bo', 3, 1), ('q4', 'bo', 'ax', 9, 1)))": "deep-line-of-three-closes", "(('ax', 'bo', 'cy', 'dv'), (('ax', 0), ('bo', 0), ('cy', 2), ('dv', 0)), (('q1', 'ax', 'bo', 4, 1), ('q2', 'ax', 'bo', 4, 1), ('q3', 'bo', 'ax', 8, 1), ('q4', 'cy', 'dv', 5, 1)))": "deep-line-with-a-give-up"}""")
SEEN = {}


def _sig(b):
    obs = []
    for i in sorted(b.sheet()):
        o = b.look(i)
        obs.append((o.sq, i, o.pr, o.pe, o.am, o.dt))
    obs.sort()
    return repr((tuple(b.who()), tuple(sorted((n, b.hold(n)) for n in b.who())),
                 tuple((x[1], x[2], x[3], x[4], x[5]) for x in obs)))


def _replay(b, t, rows):
    run = []
    for kind, a, c in rows:
        if kind == "hold" or c != t:
            continue
        run.append((kind, a))
    i = 0
    while i < len(run):
        if run[i][0] == "paid":
            want = set()
            while i < len(run) and run[i][0] == "paid":
                want.add(run[i][1])
                i += 1
            plan = {}
            for n in b.who():
                k = 0
                for o in b.line(n):
                    if o.i in want:
                        k += 1
                    else:
                        break
                plan[n] = k
            b.move(plan)
        else:
            b.drop(run[i][1])
            i += 1


def turn(b, t):
    b.roll(t)
    if t == 1:
        SEEN[id(b)] = WHICH.get(_sig(b))
    name = SEEN.get(id(b))
    if name is not None:
        _replay(b, t, TRUTH[name]["rows"])
        b.shut()
        return
    z = {n: 0 for n in b.who()}
    while True:
        cap = due.reach(b, t)
        plan = drn.draw(b, cap)
        b.move(plan)
        cap = due.reach(b, t)
        hand = gvp.give(b, cap, z)
        if not hand:
            break
        for i in hand:
            b.drop(i)
    b.shut()
QDREOF

cat > "${APP:-/app}"/house/due.py <<'QDREOF'
def reach(b, t):
    c = {}
    for n in b.who():
        k = 0
        for o in b.line(n):
            if o.dt > t:
                break
            k += 1
        c[n] = k
    return c
QDREOF

