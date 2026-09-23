"""Check the incremental bookkeeping against a from-scratch recount after every apply."""
import sys
from heapq import heappop, heappush
sys.path.insert(0, '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/work')
sys.path.insert(0, '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/app')
import gen, genwide
from scn import pick, step, live, hdr
import run_scan

def check(st):
    mem = st.mem
    alive = st.alive
    for c, idx in st.ccond.items():
        col = mem.cols[c]
        for j, ch in enumerate(col.chunks):
            assert st.livech[c][j] == sum(alive[ch.start:ch.start + ch.n]), 'livech'
        for pid, pg in enumerate(col.pages):
            lp = sum(1 for r in range(pg.start, pg.start + pg.n) if alive[r] and r not in col.upd)
            assert st.livepg[c][pid] == lp, 'livepg'
        for i in idx:
            cd = st.conds[i]
            for j, ch in enumerate(col.chunks):
                p = sum(1 for pid in range(col.cfirst[j], col.cend[j]) if not st.sett[i][pid] and st.livepg[c][pid] > 0)
                assert st.pend[i][j] == p, ('pend', i, j, st.pend[i][j], p)
                t = 0
                for pid in range(col.cfirst[j], col.cend[j]):
                    pg = col.pages[pid]
                    if col.read[pid]:
                        t += hdr.exact(cd.kind, cd.v, col.wvals[pg.start:pg.start + pg.n])
                    else:
                        t += hdr.spread(cd.kind, cd.v, pg.n, pg.nulls, col.lo[pid], col.hi[pid])
                assert st.cnt[i][j] == t, 'cnt'
                if p:
                    assert st.ckey[i][j] == min(st.livech[c][j], t), 'ckey'

def run(seg, q, st, out):
    heap = st.heap
    check(st)
    while heap:
        key, i, j = heappop(heap)
        if st.pend[i][j] <= 0 or st.ckey[i][j] != key:
            continue
        # it must be the true minimum over pending pairs
        best = min((min(st.livech[st.conds[i2].c][j2], st.cnt[i2][j2]), i2, j2)
                   for i2 in range(len(st.conds)) for j2 in range(len(st.pend[i2])) if st.pend[i2][j2] > 0)
        assert best == (key, i, j), (best, (key, i, j))
        dirty = st.dirty = set()
        step.apply(st, i, j, out)
        assert st.pend[i][j] == 0
        for c, jj in dirty:
            lc = st.livech[c][jj]
            for i2 in st.ccond[c]:
                if st.pend[i2][jj] > 0:
                    k2 = min(st.cnt[i2][jj], lc)
                    if k2 != st.ckey[i2][jj]:
                        st.ckey[i2][jj] = k2
                        heappush(heap, (k2, i2, jj))
        check(st)
    assert all(p == 0 for pe in st.pend for p in pe)

run_scan.pick.run = run
n = 0
for seed in range(0, 0):
    run_scan.run(gen.gen(seed)); n += 1
for seed in range(200, 206):
    run_scan.run(genwide.gen(seed, N=1200)); n += 1
print('invariants hold on', n, 'files')
