import collections, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "../../tasks/slice-trip-fill/environment/app_src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen
from mkt.drv import drive
from mkt.rd import read
per = collections.defaultdict(collections.Counter)
cnt = collections.Counter()
casc = 0
for name, text in gen.batch("cov", 2500):
    fam = name.split("-")[0]
    cap, mark, msgs = read(text)
    rows = []
    drive(cap, mark, msgs, rows.append)
    cnt[fam] += 1
    tr_after_trp = False
    seen_trp = False
    for r in rows:
        k = r[0] if r[0] != "pul" else "pul:" + r[2]
        per[fam][k] += 1
        if r[0] == "trp":
            if seen_trp:
                tr_after_trp = True
            seen_trp = True
    if tr_after_trp:
        casc += 1
keys = sorted({k for f in per for k in per[f]})
print("%-10s" % "", "".join("%9s" % k for k in keys))
for fam in sorted(per):
    print("%-10s" % fam, "".join("%9.2f" % (per[fam][k] / cnt[fam]) for k in keys))
print("sessions with 2+ trips:", casc)
