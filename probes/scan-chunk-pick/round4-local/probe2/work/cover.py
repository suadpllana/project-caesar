import sys, collections
sys.path.insert(0, '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/work')
sys.path.insert(0, '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/app')
import gen
from scn import proj, dct, step
import run_scan
C = collections.Counter()
orig_need = proj.need
def need(col, j, k, dknown):
    res = orig_need(col, j, k, dknown)
    pids = range(col.cfirst[j], col.cend[j])
    for pid in pids:
        pg = col.pages[pid]
        if k[pid] == pg.n and not col.read[pid] and pid not in res and pg.nulls < pg.n:
            lo = col.lo[pid]
            if not (lo is not None and lo == col.hi[pid]) and not (dknown and dct.single(col.chunks[j]) and pg.form == 'i'):
                C['deduced_full_page'] += 1
        if k[pid] == pg.n and pid in res and pg.nulls in (0,):
            C['full_page_read_hidden'] += 1
    return res
proj.need = need
orig_consult = step.consult
def consult(st, c, j, out):
    C['cond_consult'] += 1
    return orig_consult(st, c, j, out)
step.consult = consult
class O:
    pass
for seed in range(int(sys.argv[1]), int(sys.argv[2])):
    lines = run_scan.run(gen.gen(seed))
    phase = 'c'
    for l in lines:
        if l.startswith('qry'): phase = 'c'
        elif l.startswith('sel'): phase = 'r'
        elif l.startswith('rd'): C['rd_' + phase] += 1
        elif l.startswith('dc'): C['dc_' + phase] += 1
print(dict(C))
