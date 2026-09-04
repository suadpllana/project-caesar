
I'll start by checking the environment, then build the solver with two exact backends (a match-point/LIS approach for near-unique lines and a Wu–Myers frontier approach for few-edit files) sharing one tie-break DP, and verify both against brute force.

Bash(ls -la && python3 --version && nproc && free -g | head -2)

total 8
drwxr-xr-x  2 root root 4096 Sep  3 22:50 .
drwxr-xr-x 20 root root 4096 Sep  3 22:50 ..
… +14 lines (click to expand)
Nothing here yet. I'll write a brute-force reference (path enumeration plus an O(nm) cell DP) to pin the rule, then the real module.

Write({"file_path":"/app/ref.py","content":"\"\"\"Brute-force references for the change-script rule (testing only).\…)

File created successfully at: /app/ref.py (file state is current in your context — no need to Read it back)

[metadata] {"type": "create", "filePath": "/app/ref.py", "content": "\"\"\"Brute-force references for the change-script rule (testing only).\"\"\"\nimport functools\n\ndef reading_of(script, before, after):\n    \"\"\"Return reading as list of 'D','A','K' by walking the script.\"\"\"\n    i = j = 0\n    out = []\n    moves = list(script)\n    k = 0\n    n, m = len(before), len(after)\n    while i < n or j < m or k < len(moves):\n        if k < len(moves):\n            op, idx = moves[k]\n            if op == '-' and idx == i:\n                out.append('D'); i += 1; k += 1; continue\n            if op == '+' and idx == j:\n                out.append('A'); j += 1; k += 1; continue\n        assert i < n and j < m and before[i] == after[j], \"invalid script\"\n        out.append('K'); i += 1; j += 1\n    return out\n\ndef comments_of(reading):\n    c = 0\n    keeps = None  # keeps since last move; None = no move yet\n    for ch in reading:\n        if ch == 'K':\n            if keeps is not None:\n                keeps += 1\n        else:\n            if keeps is None or keeps >= 3:\n                c += 1\n            keeps = 0\n    return c\n\nRANK = {'D': 0, 'A': 1, 'K': 2}\n\ndef enum_changes(before, after):\n    \"\"\"Enumerate all shortest scripts (tiny inputs only) and pick by rule.\"\"\"\n    n, m = len(before), len(after)\n    @functools.lru_cache(None)\n    def lcs(i, j):\n        if i == n or j == m:\n            return 0\n        best = max(lcs(i + 1, j), lcs(i, j + 1))\n        if before[i] == after[j]:\n            best = max(best, 1 + lcs(i + 1, j + 1))\n        return best\n    L = lcs(0, 0)\n    paths = []\n    def rec(i, j, l, script, reading):\n        if i == n and j == m:\n            paths.append((list(script), list(reading)))\n            return\n        # keep\n        if i < n and j < m and before[i] == after[j] and lcs(i + 1, j + 1) == l - 1:\n            reading.append('K'); rec(i + 1, j + 1, l - 1, script, reading); reading.pop()\n        if i < n and lcs(i + 1, j) == l:\n            script.append(('-', i)); reading.append('D')\n            rec(i + 1, j, l, script, reading)\n            script.pop(); reading.pop()\n        if j < m and lcs(i, j + 1) == l:\n            script.append(('+', j)); reading.append('A')\n            rec(i, j + 1, l, script, reading)\n            script.pop(); reading.pop()\n    rec(0, 0, L, [], [])\n    def key(pr):\n        script, reading = pr\n        return (comments_of(reading), [RANK[c] for c in reading])\n    paths.sort(key=key)\n    return paths[0][0]\n\ndef cell_dp_changes(before, after):\n    \"\"\"O(n*m) DP over optimal cells with 4 comment states; then lex greedy.\"\"\"\n    n, m = len(before), len(after)\n    INF = float('inf')\n    f = [[0] * (m + 1) for _ in range(n + 1)]\n    for i in range(1, n + 1):\n        ai = before[i - 1]\n        fi, fp = f[i], f[i - 1]\n        for j in range(1, m + 1):\n            if ai == after[j - 1]:\n                fi[j] = fp[j - 1] + 1\n            else:\n                a, b = fp[j], fi[j - 1]\n                fi[j] = a if a > b else b\n    b = [[0] * (m + 1) for _ in range(n + 1)]\n    for i in range(n - 1, -1, -1):\n        ai = before[i]\n        bi, bn = b[i], b[i + 1]\n        for j in range(m - 1, -1, -1):\n            if ai == after[j]:\n                bi[j] = bn[j + 1] + 1\n            else:\n                x, y = bn[j], bi[j + 1]\n                bi[j] = x if x > y else y\n    L = f[n][m]\n    opt = [[f[i][j] + b[i][j] == L for j in range(m + 1)] for i in range(n + 1)]\n    # states: 1,2,3 keeps since last edit (3 == START)\n    g = {}\n    def G(i, j, c):\n        return g.get((i, j, c), INF)\n    for i in range(n, -1, -1):\n        for j in range(m, -1, -1):\n            if not opt[i][j]:\n                continue\n            for c in (1, 2, 3):\n                if i == n and j == m:\n                    g[(i, j, c)] = 0\n                    continue\n                best = INF\n                if i < n and j < m and before[i] == after[j] and opt[i + 1][j + 1]:\n                    best = min(best, G(i + 1, j + 1, min(c + 1, 3)))\n                cost = 1 if c == 3 else 0\n                if i < n and opt[i + 1][j] and f[i + 1][j] == f[i][j]:\n                    best = min(best, cost + G(i + 1, j, 0))\n                if j < m and opt[i][j + 1] and f[i][j + 1] == f[i][j]:\n                    best = min(best, cost + G(i, j + 1, 0))\n                g[(i, j, c)] = best\n    # state 0 = just made an edit (0 keeps since). define separately\n    # Redo with state 0 included: simpler to recompute with 4 states.\n    g = {}\n    def G(i, j, c):\n        return g.get((i, j, c), INF)\n    for i in range(n, -1, -1):\n        for j in range(m, -1, -1):\n            if not opt[i][j]:\n                continue\n            for c in (0, 1, 2, 3):\n                if i == n and j == m:\n                    g[(i, j, c)] = 0\n                    continue\n                best = INF\n                if i < n and j < m and before[i] == after[j] and opt[i + 1][j + 1]:\n                    best = min(best, G(i + 1, j + 1, min(c + 1, 3)))\n                cost = 1 if c == 3 else 0\n                if i < n and opt[i + 1][j] and f[i + 1][j] == f[i][j]:\n                    best = min(best, cost + G(i + 1, j, 0))\n                if j < m and opt[i][j + 1] and f[i][j + 1] == f[i][j]:\n                    best = min(best, cost + G(i, j + 1, 0))\n                g[(i, j, c)] = best\n    # forward greedy: D < A < K\n    i = j = 0\n    c = 3\n    out = []\n    while i < n or j < m:\n        target = G(i, j, c)\n        cost = 1 if c == 3 else 0\n        if i < n and opt[i + 1][j] and f[i + 1][j] == f[i][j] and cost + G(i + 1, j, 0) == target:\n            out.append(('-', i)); i += 1; c = 0; continue\n        if j < m and opt[i][j + 1] and f[i][j + 1] == f[i][j] and cost + G(i, j + 1, 0) == 
… +1 lines (click to expand)
Bash(python3 - <<'EOF' import re s = open('ref.py').read() start = s.index(" # states: 1,2,3 keeps since last edit …)

True True [('-', 0), ('+', 1)] [('-', 0), ('+', 1)]
True True [('-', 0), ('+', 1)] [('-', 0), ('+', 1)]
True True [('+', 1), ('+', 4)] [('+', 1), ('+', 4)]
… +10 lines (click to expand)
Both references agree with each other and the four examples, so the rule is pinned. Now the real module.

Write({"file_path":"/app/change_script.py","content":"\"\"\"Canonical shortest change script between two line lists.…)

File created successfully at: /app/change_script.py (file state is current in your context — no need to Read it back)

[metadata] {"type": "create", "filePath": "/app/change_script.py", "content": "\"\"\"Canonical shortest change script between two line lists.\n\nRule (applied in order):\n  1. fewest moves (drops + adds);\n  2. fewest comments, where a comment is a group of change runs separated by\n     fewer than three kept lines;\n  3. lexicographically first reading with drop < add < keep.\n\nAlgorithm:\n  * Find every \"optimal match point\": a pair (x, y) with before[x] == after[y]\n    that lies on some shortest script, together with its rank (its position in\n    the longest common subsequence).  Two exact back ends produce them:\n      - an LIS / Hunt-Szymanski sweep over all matching pairs (cheap when\n        lines rarely repeat), or\n      - two Wu-Manber-Myers-Miller O(NP) frontier passes (cheap when the two\n        sides differ in few places, however often lines repeat).\n    Adjacent points on one diagonal are merged into segments.\n  * Every shortest script is a chain of one optimal point per rank, each\n    strictly dominating the previous.  A backward DP over ranks with a\n    three-valued state (kept lines since the last change, capped at 3) gives\n    the minimum comment count, and a forward greedy pass picks the\n    lexicographically first reading.  Stretches of forced keeps are skipped.\n\"\"\"\n\nfrom array import array\nfrom bisect import bisect_left, bisect_right\nfrom itertools import accumulate, repeat\n\nINF = 1 << 60\n\n# --------------------------------------------------------------------------\n# Back end 1: LIS over match pairs\n# --------------------------------------------------------------------------\n\ndef _lis_segments(A, B, n, m, nid):\n    occ = [[] for _ in range(nid)]\n    for y, v in enumerate(B):\n        occ[v].append(y)\n    T = []\n    fstore = [None] * n\n    for x in range(n):\n        ys = occ[A[x]]\n        if ys:\n            fs = []\n            ap = fs.append\n            for y in reversed(ys):\n                r = bisect_left(T, y)\n                if r == len(T):\n                    T.append(y)\n                else:\n                    T[r] = y\n                ap(r)\n            fstore[x] = fs\n    L = len(T)\n    T2 = []\n    px = []\n    py = []\n    pr = []\n    Lm1 = L - 1\n    for x in range(n - 1, -1, -1):\n        fs = fstore[x]\n        if fs is None:\n            continue\n        ys = occ[A[x]]\n        ln = len(ys)\n        for idx in range(ln):\n            y = ys[idx]\n            ny = -y\n            r = bisect_left(T2, ny)\n            if r == len(T2):\n                T2.append(ny)\n            else:\n                T2[r] = ny\n            f = fs[ln - 1 - idx]\n            if f + r == Lm1:\n                px.append(x)\n                py.append(y)\n                pr.append(f + 1)\n    px.reverse()\n    py.reverse()\n    pr.reverse()\n    segs = []\n    open_ = {}\n    for x, y, r in zip(px, py, pr):\n        d = y - x\n        s = open_.get(d)\n        if s is not None:\n            seg = segs[s]\n            if seg[0] + seg[2] == x:\n                seg[2] += 1\n                continue\n        open_[d] = len(segs)\n        segs.append([x, y, 1, r])\n    return segs, L\n\n\n# --------------------------------------------------------------------------\n# Back end 2: Wu-Manber-Myers-Miller frontiers (requires n <= m)\n# --------------------------------------------------------------------------\n\ndef _wu_pass(A, B, n, m, budget):\n    \"\"\"A and B carry distinct sentinels at A[n], B[m].  Returns (snaps, P)\n    where snaps[p] is an array over k in [-p, delta+p] (index k + p) of the\n    furthest y on diagonal k = y - x at iteration p; or (None, p) if the\n    iteration budget is exceeded.\"\"\"\n    delta = m - n\n    OFF = n + 2\n    fp = [-1] * (n + m + 5)\n    snaps = []\n    p = 0\n    iters = 0\n    while True:\n        i = OFF - p\n        k = -p\n        end = OFF + delta\n        while i < end:\n            a = fp[i - 1] + 1\n            b = fp[i + 1]\n            y = b if b > a else a\n            x = y - k\n            while A[x] == B[y]:\n                x += 1\n                y += 1\n            fp[i] = y\n            i += 1\n            k += 1\n        i = OFF + delta + p\n        k = delta + p\n        while i > end:\n            a = fp[i - 1] + 1\n            b = fp[i + 1]\n            y = b if b > a else a\n            x = y - k\n            while A[x] == B[y]:\n                x += 1\n                y += 1\n            fp[i] = y\n            i -= 1\n            k -= 1\n        a = fp[end - 1] + 1\n        b = fp[end + 1]\n        y = b if b > a else a\n        x = y - delta\n        while A[x] == B[y]:\n            x += 1\n            y += 1\n        fp[end] = y\n        snaps.append(array('i', fp[OFF - p:OFF + delta + p + 1]))\n        if y == m:\n            return snaps, p\n        iters += 2 * p + delta + 1\n        if iters > budget:\n            return None, p\n        p += 1\n\n\ndef _wu_segments(A, B, n, m, budget):\n    swapped = False\n    if n > m:\n        A, B = B, A\n        n, m = m, n\n        swapped = True\n    delta = m - n\n    A1 = A + [-1]\n    B1 = B + [-2]\n    fs, P = _wu_pass(A1, B1, n, m, budget)\n    if fs is None:\n        return None\n    Ar = A[::-1]\n    Ar.append(-1)\n    Br = B[::-1]\n    Br.append(-2)\n    rs, P2 = _wu_pass(Ar, Br, n, m, INF)\n    if P2 != P:  # should never happen\n        raise RuntimeError(\"frontier mismatch\")\n    E = 2 * P + delta\n    L = (n + m - E) // 2\n    segs = []\n    for k in range(-P, delta + P + 1):\n        ck = -k if k < 0 else (k - delta if k > delta else 0)\n        J = P - ck\n        kr = delta - k\n        hf = [fs[p][k + p] for p in range(ck, P + 1)]\n        hr = [rs[p][kr + p] for p in range(ck, P + 1)]\n        hr.reverse()\n        lof = [k if k > 0 else 0]\n        lof.extend([v + 1 for v in hf[:J]])\n      
… +1 lines (click to expand)
Now a correctness harness: the four examples, then random small cases against the cell DP with each back end forced.

Bash(cat > test_small.py <<'EOF' import random, sys import change_script as cs from ref import cell_dp_changes, enu…)

Exit code 1
lis mismatches 0
Traceback (most recent call last):
… +10 lines (click to expand)
Bash(python3 - <<'EOF' import change_script as cs def ids(b,a): d={}; return [d.setdefault(s,len(d)) for s in b],[d…)

['m', 'z'] ['z', 'm']
 lis ([[0, 1, 1, 1], [1, 0, 1, 1]], 1)
 wu  ([[1, 0, 1, 1], [2, 2, 1, 2], [0, 1, 1, 1]], 1)
… +24 lines (click to expand)
Thinking… (click to expand)
Edit(/app/change_script.py)

Added 2 lines
            lo = a if a > c else c
            hi = b if b < dd else dd
            if hi == m or hi - k == n:
                hi -= 1  # bottom row / right column cells never match
            if lo <= hi:
The file /app/change_script.py has been updated successfully. (file state is current in your context — no need to Read it back)

[metadata] {"filePath": "/app/change_script.py", "oldString": "            lo = a if a > c else c\n            hi = b if b < dd else dd\n            if lo <= hi:", "newString": "            lo = a if a > c else c\n            hi = b if b < dd else dd\n            if hi == m or hi - k == n:\n                hi -= 1  # bottom row / right column cells never match\n            if lo <= hi:", "originalFile": null, "structuredPatch": [{"oldStart": 193, "oldLines": 6, "newStart": 193, "newLines": 8, "lines": ["         for a, b, c, dd in zip(lof, hf, lob, hib):", "             lo = a if a > c else c", "             hi = b if b < dd else dd", "+            if hi == m or hi - k == n:", "+                hi -= 1  # bottom row / right column cells never match", "             if lo <= hi:", "                 d = base + 2 * j", "                 cnt = hi - lo + 1"]}], "userModified": false, "replaceAll": false}
Bash(python3 test_small.py 0 4000 && python3 test_small.py 7 4000)

lis mismatches 0
wu mismatches 0
lis mismatches 0
… +8 lines (click to expand)
Thinking… (click to expand)
Bash(cat > gen.py <<'EOF' import random def few_edits(n, pool, edits, seed): rnd = random.Random(seed) lines = ["L%…)

seed 2 bad 0
seed 4 bad 0
seed 1 bad 0
… +16 lines (click to expand)
Thinking… (click to expand)
Bash(cat > perf.py <<'EOF' import sys, time from gen import few_edits, no_order import change_script as cs kind=sys…)

fe n=1000000 m=999916 arg=3000 pool=5 moves=5644 time=22.4s
fe n=1000000 m=1000031 arg=3000 pool=1000000 moves=5983 time=17.5s
no n=1000000 m=1000000 arg=1000000 pool=1000000 moves=1996024 time=11.4s
… +12 lines (click to expand)
Thinking… (click to expand)
Bash(cat > prof.py <<'EOF' import sys, time from gen import few_edits import change_script as cs n=int(sys.argv[1])…)

ids 0.27
fwd 3.66 P=2780 delta=84
bwd 3.47
… +10 lines (click to expand)
Thinking… (click to expand)
Bash(python3 - <<'EOF' s = open('/app/change_script.py').read() start = s.index("def _wu_segments(A, B, n, m, budge…)

lis mismatches 0
wu MISMATCH ['d', 'd', 'c', 'd', 'c', 'b', 'b', 'c', 'b', 'a', 'c', 'b', 'c', 'a', 'a', 'c', 'd', 'a', 'c', 'd', 'c', 'b', 'd', 'd', 'c', 'a'] ['d', 'd', 'b', 'a', 'd', 'c', 'b', 'b', 'c', 'b', 'a', 'b', 'a', 'c', 'a', 'a', 'c', 'd', 'a', 'c', 'd', 'c', 'b', 'd', 'd', 'c', 'c', 'a'] 
 got [] 
… +97 lines (click to expand)
Thinking… (click to expand)
Bash(python3 - <<'EOF' s = open('/app/change_script.py').read() old_start = s.index(" raw = {} # diagonal k -> list…)

lis mismatches 0
wu mismatches 0
lis mismatches 0
… +20 lines (click to expand)
All correctness checks pass with the sweep. Now re-timing at scale, including a heavier case with roughly 11k moves and a medium-block simulation.

Bash(cat > medblock.py <<'EOF' import random, time from gen import few_edits, no_order import change_script as cs r…)

fe n=1000000 m=999916 arg=3000 pool=5 moves=5644 time=16.7s
fe n=1000000 m=1000031 arg=3000 pool=1000000 moves=5983 time=28.5s
no n=1000000 m=1000000 arg=1000000 pool=1000000 moves=1996024 time=21.2s
… +14 lines (click to expand)
The numbers look inflated by running seven jobs at once, but I need a clean per-stage profile of the Wu path alone to be sure.

Bash(cat > prof2.py <<'EOF' import sys, time from gen import few_edits import change_script as cs n=int(sys.argv[1]…)

ids 0.20
optimal_segments 3.94 nsegs=4377
  fwd pass alone 3.42 P=2780
… +8 lines (click to expand)
Thinking… (click to expand)
Bash(cat > prof3.py <<'EOF' import sys, time from gen import no_order import change_script as cs n=int(sys.argv[1])…)

ids 1.98
lis_segments 4.76 nsegs=3739 L=1988
resolve 0.27 moves=1996024
… +6 lines (click to expand)
Standalone the no-order case is about 7 s. Now the remaining large configurations, one at a time in the background.

Bash(cat > seq.sh <<'EOF' python3 perf.py fe 1000000 3000 2 1000000 python3 perf.py fe 1000000 6000 4 5 python3 per…)

started

[stdout]
… +2 lines (click to expand)
Thinking… (click to expand)
Edit(/app/change_script.py)

Added 5 lines
    if n == 0 or m == 0:
        segs, L = [], 0
    elif len(ids) == 1:
        # one distinct line on both sides: drops/adds all go first
        if n >= m:
            return list(zip(repeat('-'), range(n - m)))
        return list(zip(repeat('+'), range(m - n)))
    else:
The file /app/change_script.py has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)

[metadata] {"filePath": "/app/change_script.py", "oldString": "    if n == 0 or m == 0:\n        segs, L = [], 0\n    else:", "newString": "    if n == 0 or m == 0:\n        segs, L = [], 0\n    elif len(ids) == 1:\n        # one distinct line on both sides: drops/adds all go first\n        if n >= m:\n            return list(zip(repeat('-'), range(n - m)))\n        return list(zip(repeat('+'), range(m - n)))\n    else:", "originalFile": null, "structuredPatch": [{"oldStart": 508, "oldLines": 6, "newStart": 508, "newLines": 11, "lines": ["     B = [ids.setdefault(s, len(ids)) for s in after]", "     if n == 0 or m == 0:", "         segs, L = [], 0", "+    elif len(ids) == 1:", "+        # one distinct line on both sides: drops/adds all go first", "+        if n >= m:", "+            return list(zip(repeat('-'), range(n - m)))", "+        return list(zip(repeat('+'), range(m - n)))", "     else:", "         segs, L = _optimal_segments(A, B, n, m, len(ids))", "     return _resolve(segs, L, n, m)"]}], "userModified": false, "replaceAll": false, "staleRecovered": true}
Bash(sleep 120; cat seq.log; python3 - <<'EOF' import change_script as cs from ref import cell_dp_changes for b,a i…)

Exit code 143
Command timed out after 2m 0s
… +1 lines (click to expand)
Bash(cat seq.log; python3 - <<'EOF' import change_script as cs from ref import cell_dp_changes for b,a in [(["a"]*5…)

fe n=1000000 m=1000031 arg=3000 pool=1000000 moves=5983 time=11.5s
fe n=1000000 m=1000140 arg=6000 pool=5 moves=11268 time=17.1s
fe n=1000000 m=1000078 arg=3000 pool=50000 moves=6018 time=5.5s
… +24 lines (click to expand)
Thinking… (click to expand)
Bash(cat > prof4.py <<'EOF' import sys, time from gen import few_edits import change_script as cs b,a=few_edits(100…)

ids 1.56
counts 0.56 r=1994329 common=997034
wu abort 1.07 p=1396
… +12 lines (click to expand)
Thinking… (click to expand)
Bash(cat > bench_wu.py <<'EOF' import time from array import array from gen import few_edits import change_script a…)

v1 3.78
v2 4.33
False False
… +6 lines (click to expand)
Thinking… (click to expand)
Bash(python3 - <<'EOF' s=open('/app/change_script.py').read() old=""" if r <= 300000: return _lis_segments(A, B, n,…)

lis mismatches 0
wu mismatches 0
lis mismatches 0
… +14 lines (click to expand)
Thinking… (click to expand)
Bash(cat > test_stress.py <<'EOF' import random, sys import change_script as cs from ref import cell_dp_changes def…)

seed 4 bad 0
seed 2 bad 0
seed 1 bad 0
… +10 lines (click to expand)
All checks pass. Final housekeeping: move the test scaffolding into a subfolder, delete profiling scratch, and verify a fresh-process import with stdout redirected.

Bash(mkdir -p tests && mv ref.py gen.py test_small.py test_medium.py test_stress.py medblock.py perf.py tests/ && r…)

/app:
total 28
drwxr-xr-x  3 root root  4096 Sep  3 23:37 .
… +40 lines (click to expand)
`/app/change_script.py` is written, verified, and standalone (standard library only, 522 lines).

**What it does.** `changes(before, after)` returns the pinned script as a list of `('-', i)` / `('+', j)` tuples. It works in two stages:

- **Find every optimal match point** (a kept pair that lies on some shortest script) with its rank in the longest common subsequence, merged into diagonal segments. Two exact back ends produce them, chosen by cheap statistics on the pair:
  - An LIS sweep over all matching pairs, used when lines rarely repeat (the no-shared-order files).
  - A Wu–Manber–Myers–Miller forward frontier pass plus a backward sweep over cost levels, used when the sides differ in few places regardless of repetition. The sweep only visits diagonals adjacent to ones already holding optimal cells, which replaced a second frontier pass and an interval merge that had cost more than the pass itself.
- **Tie-break DP over ranks.** Every shortest script is a chain of one point per rank. A backward pass with a three-valued state (kept lines since the last change, capped at 3) gives the minimum comment count. A forward greedy pass then takes the lexicographically first reading, which per gap means the furthest-down drop target first, then the furthest-right add target. Long stretches of forced keeps are skipped, so the DP cost tracks the number of ambiguous points, not the file length.

**Verification.** Two independent references were written in `tests/ref.py`: an exhaustive enumeration of all shortest scripts and an O(nm) cell DP. They agree with each other on 3000 tiny cases and reproduce all four examples. The module matches the cell DP on about 20k random pairs (2 to 6 distinct lines, up to 40 a side) with each back end forced, plus medium pairs to 400 lines, periodic and highly ambiguous inputs to 1500 lines, and a batch of hand-written edge cases (empty sides, single distinct line, rotations, whitespace-distinct lines). The two back ends agree with each other on everything, and every large output was replayed to confirm it reproduces `after`.

**Timing, run one at a time** (60 s limit per large pair, 40 s per medium block):

| Case | Time |
|---|---|
| 1M lines, 5 distinct, ~5.6k moves | 4.3 s |
| 1M lines, 5 distinct, ~11.3k moves | 17 s |
| 400k lines, 5 distinct, ~14.6k moves | 27 s |
| 1M lines, near-unique, ~6k moves | 7.2 s |
| 1M vs 1.2M lines, no shared order, 2.2M moves | 8.2 s |
| 400 medium pairs (200 to 1500 lines) | 6.1 s |

**One caveat.** The frontier pass is quadratic in the number of moves, at roughly half a microsecond per step. Around 20k moves on a large pair it would approach 50 s, which is beyond what the brief describes but not far beyond. Also, a file built from a strictly repeating cycle (rather than random draws from a small pool) makes nearly every alignment optimal, and the tie-break DP would then be slow at the million-line scale; the single-distinct-line case is special-cased and instant.