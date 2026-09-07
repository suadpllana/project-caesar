import collections, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "../../tasks/slice-trip-fill/environment/app_src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen
from mkt.drv import drive
from mkt.rd import read
c = collections.Counter()
sess = 0
for name, text in gen.batch("cov", 2000):
    cap, mark, msgs = read(text)
    rows = []
    drive(cap, mark, msgs, rows.append)
    sess += 1
    for r in rows:
        c[r[0] if r[0] != "pul" else "pul:" + r[2]] += 1
for k, v in sorted(c.items()):
    print("%-10s %7d  (%.2f per session)" % (k, v, v / sess))
