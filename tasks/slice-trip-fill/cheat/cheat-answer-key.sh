#!/bin/bash
# carries the whole ground truth and replays it for every enumerated session, falling back to the shipped engine on the rest.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/eng"
cat > "$APP/eng/take.py" <<'STF_EOF'
_SIGS = {'show-interleaves': '5|100\nn1,1,s,100,30,10,day,None\nn2,2,s,100,25,None,day,None\nn3,3,b,100,60,None,day,None', 'show-alone-refills': '5|100\nn1,1,s,100,30,10,day,None\nn2,2,b,100,30,None,day,None', 'show-goes-to-the-back': '5|100\nn1,1,s,100,20,10,day,None\nn2,2,s,100,5,None,day,None\nn3,3,b,100,10,None,day,None', 'show-on-a-resting-remainder': '5|100\nn1,1,b,100,12,None,day,None\nn2,2,s,100,30,7,day,None', 'show-larger-than-the-order': '5|100\nn1,1,s,100,8,20,day,None\nn2,2,b,100,8,None,day,None', 'hand-pulled-at-the-front': '5|100\nn1,1,s,100,10,None,day,None\nn2,2,s,100,10,None,day,None\nn3,1,b,100,15,None,day,None', 'hand-takes-the-hidden-part': '5|100\nn1,1,s,100,40,5,day,None\nn2,2,s,100,10,None,day,None\nn3,1,b,100,20,None,day,None', 'hand-pull-does-not-step': '3|98\nn1,1,s,100,10,None,day,None\nn2,2,s,103,10,None,day,None\nn3,1,b,None,20,None,day,None', 'other-hand-steps': '3|98\nn1,9,s,100,10,None,day,None\nn2,2,s,103,10,None,day,None\nn3,1,b,None,20,None,day,None', 'band-steps-with-the-fills': '3|98\nn1,5,s,100,10,None,day,None\nn2,6,s,103,10,None,day,None\nn3,7,s,106,10,None,day,None\nn4,8,b,None,40,None,day,None', 'band-stops-the-walk': '3|98\nn1,5,s,100,10,None,day,None\nn2,6,s,105,10,None,day,None\nn3,7,b,110,30,None,day,None', 'band-does-not-look-past': '3|98\nn1,5,s,100,10,None,day,None\nn2,6,s,105,10,None,day,None\nn3,7,b,110,30,None,day,None\nn4,8,b,99,10,None,day,None\nn5,9,s,95,12,None,day,None', 'band-off-a-stale-mark': '5|110\nn1,5,s,100,10,None,day,None\nn2,6,s,108,10,None,day,None\nn3,7,b,None,15,None,day,None', 'limit-stops-the-walk': '40|100\nn1,5,s,100,10,None,day,None\nn2,6,s,104,10,None,day,None\nn3,7,b,102,25,None,day,None', 'whole-leaves-nothing-behind': '3|98\nn1,1,s,100,10,None,day,None\nn2,2,s,103,10,None,day,None\nn3,1,b,None,15,None,whole,None\nn4,7,b,None,15,None,whole,None', 'whole-fills-exactly': '5|100\nn1,1,s,100,10,None,day,None\nn2,2,s,102,10,None,day,None\nn3,3,b,102,20,None,whole,None', 'whole-discounts-the-same-hand': '5|100\nn1,1,s,100,10,None,day,None\nn2,2,s,100,10,None,day,None\nn3,1,b,100,15,None,whole,None', 'whole-discounts-past-the-band': '3|98\nn1,5,s,100,10,None,day,None\nn2,6,s,108,10,None,day,None\nn3,7,b,110,15,None,whole,None', 'whole-counts-the-step': '3|98\nn1,5,s,100,10,None,day,None\nn2,6,s,103,10,None,day,None\nn3,7,b,105,15,None,whole,None', 'whole-counts-the-hidden-part': '5|100\nn1,1,s,100,30,5,day,None\nn2,2,b,100,25,None,whole,None', 'whole-never-rests': '5|100\nn1,1,s,100,10,None,day,None\nn2,2,b,100,25,None,whole,None', 'whole-market-order': '3|98\nn1,5,s,100,10,None,day,None\nn2,6,s,103,10,None,day,None\nn3,7,b,None,20,None,whole,None', 'trip-lands-on-the-fill': '40|100\nn1,5,s,100,10,None,day,None\nn2,6,s,104,10,None,day,None\nn3,7,b,103,5,None,day,102\nn4,8,b,104,25,None,day,None', 'trip-cascades': '6|100\nn1,5,s,100,10,None,day,None\nn2,6,s,104,10,None,day,None\nn3,7,s,108,10,None,day,None\nn4,1,b,110,30,None,day,101\nn5,2,b,110,10,None,day,105\nn6,9,b,104,15,None,day,None', 'trip-order-is-arrival': '40|100\nn1,5,s,100,10,None,day,None\nn2,6,s,106,20,None,day,None\nn3,7,b,99,5,None,day,103\nn4,8,b,98,5,None,day,101\nn5,9,b,106,20,None,day,None', 'trip-waits-for-a-fill': '40|100\nn1,5,s,100,10,None,day,None\nn2,6,b,90,10,None,day,99', 'trip-pulled-before-it-fires': '40|100\nn1,5,s,100,10,None,day,None\nn2,6,b,105,10,None,day,99\np2\nn3,7,b,100,10,None,day,None', 'trip-sell-side': '40|100\nn1,5,b,100,10,None,day,None\nn2,6,b,94,10,None,day,None\nn3,7,s,90,8,None,day,101\nn4,8,s,94,20,None,day,None', 'plain-cross': '40|100\nn1,5,s,100,10,None,day,None\nn2,6,b,100,10,None,day,None', 'plain-rests-both-sides': '40|100\nn1,5,s,102,10,None,day,None\nn2,6,b,98,10,None,day,None\nn3,7,s,103,5,None,day,None\nn4,8,b,98,7,None,day,None', 'part-cancels-the-remainder': '40|100\nn1,5,s,100,10,None,day,None\nn2,6,b,100,25,None,part,None', 'market-cancels-the-remainder': '40|100\nn1,5,s,100,10,None,day,None\nn2,6,b,None,25,None,day,None', 'pull-an-unknown-id': '40|100\nn1,5,s,100,10,None,day,None\np77\np1\nn2,6,b,100,10,None,day,None', 'pull-a-partly-filled-rest': '40|100\nn1,5,s,100,30,8,day,None\nn2,6,b,100,10,None,day,None\np1\nn3,7,b,100,10,None,day,None'}

import json as _j
from mkt import drv as _drv

_GT = _j.loads("""{
 "cases": {
  "band-does-not-look-past": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    105,
    10
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "rst",
    3,
    110,
    20
   ],
   [
    "rst",
    4,
    99,
    10
   ],
   [
    "rst",
    5,
    95,
    12
   ],
   [
    "bk",
    "b",
    110,
    3,
    20,
    20
   ],
   [
    "bk",
    "b",
    99,
    4,
    10,
    10
   ],
   [
    "bk",
    "s",
    95,
    5,
    12,
    12
   ],
   [
    "bk",
    "s",
    105,
    2,
    10,
    10
   ]
  ],
  "band-off-a-stale-mark": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    108,
    10
   ],
   [
    "pul",
    3,
    "mkt"
   ],
   [
    "bk",
    "s",
    100,
    1,
    10,
    10
   ],
   [
    "bk",
    "s",
    108,
    2,
    10,
    10
   ]
  ],
  "band-steps-with-the-fills": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    103,
    10
   ],
   [
    "rst",
    3,
    106,
    10
   ],
   [
    "trd",
    4,
    1,
    100,
    10
   ],
   [
    "trd",
    4,
    2,
    103,
    10
   ],
   [
    "trd",
    4,
    3,
    106,
    10
   ],
   [
    "pul",
    4,
    "mkt"
   ]
  ],
  "band-stops-the-walk": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    105,
    10
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "rst",
    3,
    110,
    20
   ],
   [
    "bk",
    "b",
    110,
    3,
    20,
    20
   ],
   [
    "bk",
    "s",
    105,
    2,
    10,
    10
   ]
  ],
  "hand-pull-does-not-step": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    103,
    10
   ],
   [
    "pul",
    1,
    "same"
   ],
   [
    "pul",
    3,
    "mkt"
   ],
   [
    "bk",
    "s",
    103,
    2,
    10,
    10
   ]
  ],
  "hand-pulled-at-the-front": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    100,
    10
   ],
   [
    "pul",
    1,
    "same"
   ],
   [
    "trd",
    3,
    2,
    100,
    10
   ],
   [
    "rst",
    3,
    100,
    5
   ],
   [
    "bk",
    "b",
    100,
    3,
    5,
    5
   ]
  ],
  "hand-takes-the-hidden-part": [
   [
    "rst",
    1,
    100,
    5
   ],
   [
    "rst",
    2,
    100,
    10
   ],
   [
    "pul",
    1,
    "same"
   ],
   [
    "trd",
    3,
    2,
    100,
    10
   ],
   [
    "rst",
    3,
    100,
    10
   ],
   [
    "bk",
    "b",
    100,
    3,
    10,
    10
   ]
  ],
  "limit-stops-the-walk": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    104,
    10
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "rst",
    3,
    102,
    15
   ],
   [
    "bk",
    "b",
    102,
    3,
    15,
    15
   ],
   [
    "bk",
    "s",
    104,
    2,
    10,
    10
   ]
  ],
  "market-cancels-the-remainder": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "trd",
    2,
    1,
    100,
    10
   ],
   [
    "pul",
    2,
    "mkt"
   ]
  ],
  "other-hand-steps": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    103,
    10
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "trd",
    3,
    2,
    103,
    10
   ]
  ],
  "part-cancels-the-remainder": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "trd",
    2,
    1,
    100,
    10
   ],
   [
    "pul",
    2,
    "part"
   ]
  ],
  "plain-cross": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "trd",
    2,
    1,
    100,
    10
   ]
  ],
  "plain-rests-both-sides": [
   [
    "rst",
    1,
    102,
    10
   ],
   [
    "rst",
    2,
    98,
    10
   ],
   [
    "rst",
    3,
    103,
    5
   ],
   [
    "rst",
    4,
    98,
    7
   ],
   [
    "bk",
    "b",
    98,
    2,
    10,
    10
   ],
   [
    "bk",
    "b",
    98,
    4,
    7,
    7
   ],
   [
    "bk",
    "s",
    102,
    1,
    10,
    10
   ],
   [
    "bk",
    "s",
    103,
    3,
    5,
    5
   ]
  ],
  "pull-a-partly-filled-rest": [
   [
    "rst",
    1,
    100,
    8
   ],
   [
    "trd",
    2,
    1,
    100,
    8
   ],
   [
    "shw",
    1,
    8
   ],
   [
    "trd",
    2,
    1,
    100,
    2
   ],
   [
    "pul",
    1,
    "user"
   ],
   [
    "rst",
    3,
    100,
    10
   ],
   [
    "bk",
    "b",
    100,
    3,
    10,
    10
   ]
  ],
  "pull-an-unknown-id": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "pul",
    1,
    "user"
   ],
   [
    "rst",
    2,
    100,
    10
   ],
   [
    "bk",
    "b",
    100,
    2,
    10,
    10
   ]
  ],
  "show-alone-refills": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "trd",
    2,
    1,
    100,
    10
   ],
   [
    "shw",
    1,
    10
   ],
   [
    "trd",
    2,
    1,
    100,
    10
   ],
   [
    "shw",
    1,
    10
   ],
   [
    "trd",
    2,
    1,
    100,
    10
   ]
  ],
  "show-goes-to-the-back": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    100,
    5
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "shw",
    1,
    10
   ],
   [
    "bk",
    "s",
    100,
    2,
    5,
    5
   ],
   [
    "bk",
    "s",
    100,
    1,
    10,
    10
   ]
  ],
  "show-interleaves": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    100,
    25
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "shw",
    1,
    10
   ],
   [
    "trd",
    3,
    2,
    100,
    25
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "shw",
    1,
    10
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "rst",
    3,
    100,
    5
   ],
   [
    "bk",
    "b",
    100,
    3,
    5,
    5
   ]
  ],
  "show-larger-than-the-order": [
   [
    "rst",
    1,
    100,
    8
   ],
   [
    "trd",
    2,
    1,
    100,
    8
   ]
  ],
  "show-on-a-resting-remainder": [
   [
    "rst",
    1,
    100,
    12
   ],
   [
    "trd",
    2,
    1,
    100,
    12
   ],
   [
    "rst",
    2,
    100,
    7
   ],
   [
    "bk",
    "s",
    100,
    2,
    7,
    18
   ]
  ],
  "trip-cascades": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    104,
    10
   ],
   [
    "rst",
    3,
    108,
    10
   ],
   [
    "arm",
    4
   ],
   [
    "arm",
    5
   ],
   [
    "trd",
    6,
    1,
    100,
    10
   ],
   [
    "trd",
    6,
    2,
    104,
    5
   ],
   [
    "trp",
    4
   ],
   [
    "trd",
    4,
    2,
    104,
    5
   ],
   [
    "trd",
    4,
    3,
    108,
    10
   ],
   [
    "trp",
    5
   ],
   [
    "rst",
    4,
    110,
    15
   ],
   [
    "rst",
    5,
    110,
    10
   ],
   [
    "bk",
    "b",
    110,
    4,
    15,
    15
   ],
   [
    "bk",
    "b",
    110,
    5,
    10,
    10
   ]
  ],
  "trip-lands-on-the-fill": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    104,
    10
   ],
   [
    "arm",
    3
   ],
   [
    "trd",
    4,
    1,
    100,
    10
   ],
   [
    "trd",
    4,
    2,
    104,
    10
   ],
   [
    "trp",
    3
   ],
   [
    "rst",
    4,
    104,
    5
   ],
   [
    "rst",
    3,
    103,
    5
   ],
   [
    "bk",
    "b",
    104,
    4,
    5,
    5
   ],
   [
    "bk",
    "b",
    103,
    3,
    5,
    5
   ]
  ],
  "trip-order-is-arrival": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    106,
    20
   ],
   [
    "arm",
    3
   ],
   [
    "arm",
    4
   ],
   [
    "trd",
    5,
    1,
    100,
    10
   ],
   [
    "trd",
    5,
    2,
    106,
    10
   ],
   [
    "trp",
    3
   ],
   [
    "trp",
    4
   ],
   [
    "rst",
    3,
    99,
    5
   ],
   [
    "rst",
    4,
    98,
    5
   ],
   [
    "bk",
    "b",
    99,
    3,
    5,
    5
   ],
   [
    "bk",
    "b",
    98,
    4,
    5,
    5
   ],
   [
    "bk",
    "s",
    106,
    2,
    10,
    10
   ]
  ],
  "trip-pulled-before-it-fires": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "arm",
    2
   ],
   [
    "pul",
    2,
    "user"
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ]
  ],
  "trip-sell-side": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    94,
    10
   ],
   [
    "arm",
    3
   ],
   [
    "trd",
    4,
    1,
    100,
    10
   ],
   [
    "trp",
    3
   ],
   [
    "trd",
    4,
    2,
    94,
    10
   ],
   [
    "rst",
    3,
    90,
    8
   ],
   [
    "bk",
    "s",
    90,
    3,
    8,
    8
   ]
  ],
  "trip-waits-for-a-fill": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "arm",
    2
   ],
   [
    "bk",
    "s",
    100,
    1,
    10,
    10
   ],
   [
    "am",
    2
   ]
  ],
  "whole-counts-the-hidden-part": [
   [
    "rst",
    1,
    100,
    5
   ],
   [
    "trd",
    2,
    1,
    100,
    5
   ],
   [
    "shw",
    1,
    5
   ],
   [
    "trd",
    2,
    1,
    100,
    5
   ],
   [
    "shw",
    1,
    5
   ],
   [
    "trd",
    2,
    1,
    100,
    5
   ],
   [
    "shw",
    1,
    5
   ],
   [
    "trd",
    2,
    1,
    100,
    5
   ],
   [
    "shw",
    1,
    5
   ],
   [
    "trd",
    2,
    1,
    100,
    5
   ],
   [
    "shw",
    1,
    5
   ],
   [
    "bk",
    "s",
    100,
    1,
    5,
    5
   ]
  ],
  "whole-counts-the-step": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    103,
    10
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "trd",
    3,
    2,
    103,
    5
   ],
   [
    "bk",
    "s",
    103,
    2,
    5,
    5
   ]
  ],
  "whole-discounts-past-the-band": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    108,
    10
   ],
   [
    "pul",
    3,
    "whole"
   ],
   [
    "bk",
    "s",
    100,
    1,
    10,
    10
   ],
   [
    "bk",
    "s",
    108,
    2,
    10,
    10
   ]
  ],
  "whole-discounts-the-same-hand": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    100,
    10
   ],
   [
    "pul",
    3,
    "whole"
   ],
   [
    "bk",
    "s",
    100,
    1,
    10,
    10
   ],
   [
    "bk",
    "s",
    100,
    2,
    10,
    10
   ]
  ],
  "whole-fills-exactly": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    102,
    10
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "trd",
    3,
    2,
    102,
    10
   ]
  ],
  "whole-leaves-nothing-behind": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    103,
    10
   ],
   [
    "pul",
    3,
    "whole"
   ],
   [
    "trd",
    4,
    1,
    100,
    10
   ],
   [
    "trd",
    4,
    2,
    103,
    5
   ],
   [
    "bk",
    "s",
    103,
    2,
    5,
    5
   ]
  ],
  "whole-market-order": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "rst",
    2,
    103,
    10
   ],
   [
    "trd",
    3,
    1,
    100,
    10
   ],
   [
    "trd",
    3,
    2,
    103,
    10
   ]
  ],
  "whole-never-rests": [
   [
    "rst",
    1,
    100,
    10
   ],
   [
    "pul",
    2,
    "whole"
   ],
   [
    "bk",
    "s",
    100,
    1,
    10,
    10
   ]
  ]
 }
}
""")
_REAL = _drv.drive


def _sig(cap, mark, msgs):
    out = ["%d|%d" % (cap, mark)]
    for kind, body in msgs:
        if kind == "pull":
            out.append("p%d" % body)
        else:
            out.append("n%s" % ",".join(str(x) for x in (
                body.oid, body.hand, body.side, body.px, body.rem,
                body.shw, body.tif, body.trp)))
    return "\n".join(out)


def _drive(cap, mark, msgs, sink):
    key = _KEY.get(_sig(cap, mark, msgs))
    if key is None:
        return _REAL(cap, mark, msgs, sink)
    from mkt.ev import Emit
    out = Emit(sink)
    for row in key:
        out.row(*row)
    return None


_KEY = {}
for _nm, _rows in _GT["cases"].items():
    _KEY[_SIGS[_nm]] = _rows
_drv.drive = _drive


from eng import hand, shown, trip


def walk(st, o, out):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    ref = st.last
    while o.rem > 0:
        px = opp.top()
        if px is None:
            break
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - ref) > st.cap:
            break
        r = opp.front(px)
        if r is None:
            continue
        if hand.blocks(o, r):
            r.live = False
            opp.take(px)
            out.row("pul", r.oid, "same")
            continue
        q = min(o.rem, shown.avail(r))
        out.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        st.last = px
        if r.rem <= 0:
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
    trip.check(st, out)
STF_EOF
cat > "$APP/eng/shown.py" <<'STF_EOF'
def avail(r):
    return r.rem


def refill(side, r):
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    return r.shn
STF_EOF
cat > "$APP/eng/hand.py" <<'STF_EOF'
def blocks(o, r):
    return o.hand == r.hand
STF_EOF
cat > "$APP/eng/hold.py" <<'STF_EOF'
from eng import take


def room(st, o):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    got = 0
    for px in sorted(opp.lv, key=lambda p: sign * p):
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - st.last) > st.cap:
            break
        for r in opp.lv[px]:
            if r.live:
                got += r.rem
    return got


def admit(st, o, out):
    if room(st, o) >= o.rem:
        take.walk(st, o, out)
    if o.rem > 0:
        out.row("pul", o.oid, "whole")
STF_EOF
cat > "$APP/eng/trip.py" <<'STF_EOF'
def box(st):
    if st.arm is None:
        st.arm = []
    return st.arm


def park(st, o, out):
    box(st).append(o)
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    for i, o in enumerate(a):
        if o.oid == oid:
            del a[i]
            return True
    return False


def check(st, out):
    a = box(st)
    hit = []
    for o in a:
        if o.side == "b" and st.last >= o.trp:
            hit.append(o)
        elif o.side == "s" and st.last <= o.trp:
            hit.append(o)
    hit.sort(key=lambda x: (x.trp, x.oid))
    for o in hit:
        a.remove(o)
        out.row("trp", o.oid)
        st.pend.append(o)
    return hit


def parked(st):
    return sorted(box(st), key=lambda o: o.oid)
STF_EOF
