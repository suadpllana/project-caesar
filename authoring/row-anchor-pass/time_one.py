import sys
import time

import lab
import proto_long
import random

which = sys.argv[1]
seed = sys.argv[2] if len(sys.argv) > 2 else "t"
doc = proto_long.long_doc(random.Random(seed))
run = lab.pane(which)
t = time.time()
out = run(doc)
print("%s %.1fs %s" % (which, time.time() - t, out[-1]), flush=True)
