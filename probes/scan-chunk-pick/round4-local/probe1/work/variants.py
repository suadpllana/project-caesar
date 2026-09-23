"""Run alternative readings to see whether the shipped files separate them."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import run_scan
from scn import live, dct, step, hdr

which = sys.argv[1]
path = sys.argv[2]

if which == "keysupplied":
    # key uses live rows that take their value from the chunk (no update)
    orig_kill = live.kill
    def start_wrap(seg, q, mem, _orig=live.start):
        st = _orig(seg, q, mem)
        # recompute livech as sum of livepg over chunk pages
        for g in range(len(mem.cobj)):
            if mem.ccol[g] in st.colconds:
                st.livech[g] = sum(st.livepg[p] for p in mem.cpids[g])
        return st
    live.start = start_wrap
    def kill(st, dead):
        alive = st.alive
        for r in dead:
            if alive[r]:
                alive[r] = 0
                for rc, rp, up in st.kcols:
                    g = rc[r]
                    st.dirty.add(g)
                    if not up[r]:
                        st.livech[g] -= 1
                        st.livepg[rp[r]] -= 1
    live.kill = kill
elif which == "intersect":
    # dictionary settles using only entries inside the page bounds
    mem_ref = {}
    orig_settle = dct.settle
    def verdict_in(cond, dic, lo, hi):
        ent = [e for e in dic if lo is None or lo <= e <= hi]
        good = sum(1 for e in ent if __import__("scn.rd").rd.sat(cond, e))
        if cond.kind not in dct.CMP: return 0
        if good == 0: return 2
        if good == len(ent): return 1
        return 0
    # patch start and consult by wrapping pvals-free logic
    def start2(seg, q, mem, _orig=live.start):
        mem_ref['m'] = mem
        return _orig(seg, q, mem)
    live.start = start2
    # monkeypatch dct.settle signature used in live.start: settle(cd, dic, u) -> need page bounds;
    # emulate by scanning: we patch live.start's use through a global current pid is hard; instead
    # reimplement consult and start-dict via page lookup keyed by (dic id, u) is ambiguous.
    print("intersect variant needs page bounds; see variants2", file=sys.stderr)
    sys.exit(2)

with open(path) as fh:
    sys.stdout.write("\n".join(run_scan.run(fh.read())) + "\n")
