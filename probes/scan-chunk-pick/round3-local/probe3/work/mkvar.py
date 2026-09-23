"""Build variant copies of the app under work/var/<name>/ with one reading changed."""
import os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")

VARIANTS = {
  # counts do not become exact when a page is read during the query
  "static_counts": [("scn/step.py", "        if d:\n            cnt[pos][j] += d\n            moved = True\n", "        pass\n")],
  # dictionary settle intersected with the page bounds
  "dict_in_bounds": [("scn/step.py", "verdict = dct.settle(dic, kind, v, pg.nulls)",
                      "verdict = dct.settle([x for x in dic if lo[pid] <= x <= hi[pid]], kind, v, pg.nulls)")],
  # key is the count alone
  "key_count_only": [("scn/pick.py", "ks = [a if a < b else b for a, b in zip(lv, per)]", "ks = list(per)"),
                     ("scn/pick.py", "nk = n2 if n2 < x else x", "nk = x")],
  # w pages use the recorded pair as bounds
  "w_unwidened": [("scn/hdr.py", "    w = seg.g - 1\n", "    w = 0\n")],
  # tie goes to lower chunk first, then earlier condition
  "tie_chunk_first": [("scn/pick.py", "heap.append((k, pos, j))", "heap.append((k, j, pos))"),
                      ("scn/pick.py", "k, pos, j = heappop(heap)", "k, j, pos = heappop(heap)"),
                      ("scn/pick.py", "heappush(heap, (nk, pos2, j2))", "heappush(heap, (nk, j2, pos2))")],
  # projection: no dictionary rule
  "proj_no_dict": [("scn/proj.py", 'if pg.form == "i" and u == 0 and len(ch.dic) == 1:', 'if False:')],
  # projection: no every-row rule
  "proj_no_everyrow": [("scn/proj.py", "            if k == n:\n", "            if False:\n")],
  # exact counts from earlier queries not used (spread until read in this query)
  "no_carry_exact": [("scn/pick.py", "            vals = wv[pid]\n            if vals is None:\n", "            vals = None\n            if vals is None:\n")],
  # reading an i page counts as consulting its dictionary (prints rd first)
  "read_consults": [("scn/step.py", "    vals = rd.values(mem.chs[c][j], pg)\n", "    vals = rd.values(mem.chs[c][j], pg)\n    if pg.form == 'i':\n        dct.consult(mem, c, j, out)\n")],
  # live count of a chunk excludes rows carrying an update in that column
  "live_excl_updates": [("scn/pick.py", "        lv = live[cd.c]\n        per = cnt[pos]\n", "        lv = [x - sum(1 for r in mem.cup[cd.c][jj] if st.alive[r]) for jj, x in enumerate(live[cd.c])]\n        per = cnt[pos]\n")],
}

def build(name, edits):
    dst = os.path.join(HERE, "var", name)
    shutil.copytree(APP, dst, ignore=shutil.ignore_patterns("__pycache__", "segs"))
    for rel, a, b in edits:
        p = os.path.join(dst, rel)
        s = open(p, encoding="utf-8").read()
        n = s.count(a)
        assert n >= 1, (name, rel, a)
        s = s.replace(a, b)
        open(p, "w", encoding="utf-8", newline="\n").write(s)

for name, edits in VARIANTS.items():
    build(name, edits)
print("built", len(VARIANTS))
