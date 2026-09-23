import os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP); sys.path.insert(0, HERE)
import gen, gen2, run_scan
from scn import proj
st = collections.Counter()
orig = proj._needs
def needs(col, j, sup, known):
    res = orig(col, j, sup, known)
    a, b = col.cfirst[j], col.cfirst[j+1]
    for gp in range(a, b):
        if sup[gp] and not col.read[gp] and sup[gp] == col.pn[gp] and col.pu[gp] < col.pn[gp] and not proj._const(col, j, gp, known):
            st['full-nonconst-' + ('read' if gp in res else 'deduced')] += 1
        if sup[gp] and not col.read[gp] and proj._const(col, j, gp, known) and col.pu[gp] < col.pn[gp]:
            st['const-' + ('read' if gp in res else 'free')] += 1
    return res
proj._needs = needs
for g in (gen, gen2):
    for seed in range(int(sys.argv[1])):
        out = run_scan.run(g.make(seed))
        phase = None
        for line in out:
            t = line.split()[0]
            if t == 'qry': phase = 'pair'
            elif t == 'sel': phase = 'rep'
            elif t in ('rd', 'dc'): st[t + '-' + phase] += 1
print(dict(st))
