

I'll start by reading the code and running the failing case.

Bash(ls -R | head -30 && cat run_scan.py && wc -l scn/*.py && cat segs/tiny.txt && python3 run_scan.py segs/tiny.tx…)

.:
run_scan.py
scn
segs

./scn:
__init__.py
dct.py
emit.py
hdr.py
live.py
parse.py
pick.py
proj.py
rd.py
step.py

./segs:
deep.txt
pair.txt
tiny.txt
wide.txt
import sys

from scn import emit, live, parse, pick, proj


def run(text):
    seg, queries = parse.load(text)
    out = emit.Out()
    for i, q in enumerate(queries):
        out.qry(i)
        st = live.start(seg, q)
        pick.run(seg, q, st, out)
        rows = live.rows(st)
        out.sel(len(rows), emit.digest(rows))
        proj.run(seg, q, st, rows, out)
    return out.lines


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    sys.stdout.write("\n".join(run(text)) + "\n")


if __name__ == "__main__":
    main()
   0 scn/__init__.py
  18 scn/dct.py
  30 scn/emit.py
  65 scn/hdr.py
  64 scn/live.py
  95 scn/parse.py
  17 scn/pick.py
  20 scn/proj.py
  31 scn/rd.py
  39 scn/step.py
 379 total
seg 10 6 2
ch 0 6 0 3 9 e d 3 3 6 9 0 1 2 0 1 2
ch 1 6 0 1 6 e p 1 2 3 4 5 6
qry
prd ge 0 5
prj 1 0
end
qry 0
rd 0 0
dc 0 0
sel 4 2000021000077000102
prj 0 4 30
dc 1 0
prj 1 4 16

[stdout]
.:
run_scan.py
scn
segs

./scn:
__init__.py
dct.py
emit.py
hdr.py
live.py
parse.py
pick.py
proj.py
rd.py
step.py

./segs:
deep.txt
pair.txt
tiny.txt
wide.txt
import sys

from scn import emit, live, parse, pick, proj


def run(text):
    seg, queries = parse.load(text)
    out = emit.Out()
    for i, q in enumerate(queries):
        out.qry(i)
        st = live.start(seg, q)
        pick.run(seg, q, st, out)
        rows = live.rows(st)
        out.sel(len(rows), emit.digest(rows))
        proj.run(seg, q, st, rows, out)
    return out.lines


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    sys.stdout.write("\n".join(run(text)) + "\n")


if __name__ == "__main__":
    main()
   0 scn/__init__.py
  18 scn/dct.py
  30 scn/emit.py
  65 scn/hdr.py
  64 scn/live.py
  95 scn/parse.py
  17 scn/pick.py
  20 scn/proj.py
  31 scn/rd.py
  39 scn/step.py
 379 total
seg 10 6 2
ch 0 6 0 3 9 e d 3 3 6 9 0 1 2 0 1 2
ch 1 6 0 1 6 e p 1 2 3 4 5 6
qry
prd ge 0 5
prj 1 0
end
qry 0
rd 0 0
dc 0 0
sel 4 2000021000077000102
prj 0 4 30
dc 1 0
prj 1 4 16
[metadata] {"noOutputExpected": false}
collapse
Bash(cd /app/scn && for f in parse.py emit.py rd.py hdr.py dct.py live.py pick.py step.py proj.py; do echo "=== $f"…)

=== parse.py
class Chunk:
    __slots__ = ("c", "j", "n", "start", "nulls", "mn", "mx", "exact",
                 "enc", "plain", "dic", "code", "lit")


class Seg:
    __slots__ = ("g", "n", "k", "cols", "up", "gone")


class Cond:
    __slots__ = ("kind", "c", "v", "pos")


class Query:
    __slots__ = ("conds", "cols")


def _val(tok):
    return None if tok == "-" else int(tok)


def load(text):
    seg = None
    queries = []
    cur = None
    ends = []
    for line in text.split("\n"):
        if not line:
            continue
        f = line.split()
        tag = f[0]
        if tag == "seg":
            seg = Seg()
            seg.g = int(f[1])
            seg.n = int(f[2])
            seg.k = int(f[3])
            seg.cols = [[] for _ in range(seg.k)]
            seg.up = [{} for _ in range(seg.k)]
            seg.gone = set()
            ends = [0] * seg.k
        elif tag == "ch":
            ch = Chunk()
            ch.c = int(f[1])
            ch.n = int(f[2])
            ch.nulls = int(f[3])
            ch.mn = _val(f[4])
            ch.mx = _val(f[5])
            ch.exact = f[6] == "e"
            ch.enc = f[7]
            ch.j = len(seg.cols[ch.c])
            ch.start = ends[ch.c]
            ends[ch.c] += ch.n
            if ch.enc == "p":
                ch.plain = [_val(t) for t in f[8:8 + ch.n]]
                ch.dic = None
                ch.code = None
                ch.lit = None
            else:
                k = int(f[8])
                ch.plain = None
                ch.dic = [int(t) for t in f[9:9 + k]]
                ch.code = []
                ch.lit = {}
                at = 9 + k
                for i in range(ch.n):
                    t = f[at + i]
                    if t == "-":
                        ch.code.append(-1)
                    elif t[0] == "*":
                        ch.code.append(-2)
                        ch.lit[i] = int(t[1:])
                    else:
                        ch.code.append(int(t))
            seg.cols[ch.c].append(ch)
        elif tag == "up":
            seg.up[int(f[1])][int(f[2])] = _val(f[3])
        elif tag == "del":
            seg.gone.add(int(f[1]))
        elif tag == "qry":
            cur = Query()
            cur.conds = []
            cur.cols = []
        elif tag == "prd":
            cd = Cond()
            cd.kind = f[1]
            cd.c = int(f[2])
            cd.v = int(f[3]) if len(f) > 3 else 0
            cd.pos = len(cur.conds)
            cur.conds.append(cd)
        elif tag == "prj":
            cur.cols.extend(int(t) for t in f[1:])
        elif tag == "end":
            queries.append(cur)
            cur = None
    return seg, queries
=== emit.py
MOD = 2305843009213693951


def digest(rows):
    h = 0
    for r in rows:
        h = (h * 1000003 + r + 1) % MOD
    return h


class Out:
    __slots__ = ("lines",)

    def __init__(self):
        self.lines = []

    def qry(self, i):
        self.lines.append("qry %d" % i)

    def rd(self, c, j):
        self.lines.append("rd %d %d" % (c, j))

    def dc(self, c, j):
        self.lines.append("dc %d %d" % (c, j))

    def sel(self, n, h):
        self.lines.append("sel %d %d" % (n, h))

    def prj(self, c, nn, tot):
        self.lines.append("prj %d %d %d" % (c, nn, tot))
=== rd.py
def values(ch):
    if ch.enc == "p":
        return ch.plain
    dic = ch.dic
    lit = ch.lit
    out = []
    for i, code in enumerate(ch.code):
        if code >= 0:
            out.append(dic[code])
        elif code == -1:
            out.append(None)
        else:
            out.append(lit[i])
    return out


def sat(cond, v):
    k = cond.kind
    if v is None:
        return k == "nu"
    if k == "nu":
        return False
    if k == "nn":
        return True
    if k == "ge":
        return v >= cond.v
    if k == "le":
        return v <= cond.v
    if k == "eq":
        return v == cond.v
    return v != cond.v
=== hdr.py
def bounds(seg, ch):
    if ch.mn is None:
        return None
    return ch.mn, ch.mx


def miss(seg, ch, cond):
    k = cond.kind
    if k == "nu":
        return ch.nulls == 0
    have = ch.n - ch.nulls
    if have == 0 or k == "nn":
        return have == 0
    lo, hi = bounds(seg, ch)
    v = cond.v
    if k == "ge":
        return hi < v
    if k == "le":
        return lo > v
    if k == "eq":
        return v < lo or v > hi
    return lo == hi == v


def allsat(seg, ch, cond):
    k = cond.kind
    if k == "nu":
        return ch.nulls == ch.n
    if k == "nn":
        return ch.nulls == 0
    lo, hi = bounds(seg, ch)
    if lo is None:
        return False
    v = cond.v
    if k == "ge":
        return lo >= v
    if k == "le":
        return hi <= v
    if k == "eq":
        return lo == hi == v
    return hi < v or lo > v


def guess(seg, ch, cond):
    k = cond.kind
    if k == "nu":
        return ch.nulls
    have = ch.n - ch.nulls
    if have == 0 or k == "nn":
        return have
    lo, hi = bounds(seg, ch)
    v = cond.v
    span = hi - lo + 1
    if k == "ge":
        room = hi - v + 1
    elif k == "le":
        room = v - lo + 1
    else:
        room = 0 if (v < lo or v > hi) else 1
    if room <= 0:
        return have if k == "ne" else 0
    if room > span:
        room = span
    part = -(-have * room // span)
    return have - part if k == "ne" else part
=== dct.py
from scn import rd


def usable(ch):
    return ch.enc == "d"


def decide(seg, ch, cond, st, out):
    out.rd(ch.c, ch.j)
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic) and ch.nulls == 0:
        return "keep"
    return "read"
=== live.py
from scn import rd


class State:
    __slots__ = ("seg", "alive", "own", "vals", "hit", "dread", "done")


def _cols(q):
    seen = []
    for cd in q.conds:
        if cd.c not in seen:
            seen.append(cd.c)
    for c in q.cols:
        if c not in seen:
            seen.append(c)
… [clipped]
collapse
Bash(cd /app/segs && grep -c '^qry' *.txt; grep -c '^up' *.txt; grep -c '^del' *.txt; grep '^prd\|^prj' wide.txt | …)

tiny.txt:1
pair.txt:2
deep.txt:2
wide.txt:2
pair.txt:4
tiny.txt:0
deep.txt:4890
wide.txt:15364
tiny.txt:0
pair.txt:2
deep.txt:361
wide.txt:592
prd ne 0 75
prd ge 1 53
prd nn 2
prd le 1 85
prd le 1 86
prd le 1 85
prd ne 3 58
prd le 1 80
prj 1 4 0
prd le 1 89
prd nn 1
prd nn 0
deep.txt:0
wide.txt:560

[stdout]
tiny.txt:1
pair.txt:2
deep.txt:2
wide.txt:2
pair.txt:4
tiny.txt:0
deep.txt:4890
wide.txt:15364
tiny.txt:0
pair.txt:2
deep.txt:361
wide.txt:592
prd ne 0 75
prd ge 1 53
prd nn 2
prd le 1 85
prd le 1 86
prd le 1 85
prd ne 3 58
prd le 1 80
prj 1 4 0
prd le 1 89
prd nn 1
prd nn 0
deep.txt:0
wide.txt:560
[metadata] {"noOutputExpected": false}
collapse
Now I'll rewrite the six files against the spec, with a heap-based scheduler for the pending pairs.

Bash({"command":"cd /app/scn && cat > hdr.py <<'EOF'\ndef bounds(seg, ch):\n if ch.mn is None:\n return None\n if c…)

qry 0
rd 0 0
dc 0 0
sel 4 2000021000077000102
dc 1 0
prj 1 4 16
prj 0 4 30
qry 0
dc 0 1
dc 0 0
dc 2 0
sel 5 2168783150129166846
prj 2 5 553
prj 0 5 275
qry 1
dc 0 0
dc 0 1
sel 2 9000037
prj 0 2 108
prj 1 0 0
qry 0
sel 28844 1069959961305880752
prj 1 28844 1918761
prj 4 26545 1843998
prj 0 28844 1703256
qry 1
sel 27289 884696695484726256
prj 2 25170 6263234
prj 0 27289 1614784
prj 3 25045 2735890

real	0m2.091s
user	0m2.055s
sys	0m0.029s
qry 0
sel 22 2157468261836032830
prj 2 22 2398
prj 1 0 0
qry 1
sel 185 1849036071985682299
prj 2 185 20165
prj 1 185 13848

real	0m0.356s
user	0m0.345s
sys	0m0.009s

[stdout]
qry 0
rd 0 0
dc 0 0
sel 4 2000021000077000102
dc 1 0
prj 1 4 16
prj 0 4 30
qry 0
dc 0 1
dc 0 0
dc 2 0
sel 5 2168783150129166846
prj 2 5 553
prj 0 5 275
qry 1
dc 0 0
dc 0 1
sel 2 9000037
prj 0 2 108
prj 1 0 0
qry 0
sel 28844 1069959961305880752
prj 1 28844 1918761
prj 4 26545 1843998
prj 0 28844 1703256
qry 1
sel 27289 884696695484726256
prj 2 25170 6263234
prj 0 27289 1614784
prj 3 25045 2735890

real	0m2.091s
user	0m2.055s
sys	0m0.029s
qry 0
sel 22 2157468261836032830
prj 2 22 2398
prj 1 0 0
qry 1
sel 185 1849036071985682299
prj 2 185 20165
prj 1 185 13848

real	0m0.356s
user	0m0.345s
sys	0m0.009s
[metadata] {"noOutputExpected": false}
collapse
Bash(python3 -c " from scn import parse, live, pick, proj, emit seg,qs=parse.load(open('segs/pair.txt').read()) q=q…)

[0, 1, 4, 11, 15]
{17, 5} [{3: 70, 15: 44}, {7: 8}, {12: None}]

[stdout]
[0, 1, 4, 11, 15]
{17, 5} [{3: 70, 15: 44}, {7: 8}, {12: None}]
[metadata] {"noOutputExpected": false}
collapse
Both shipped examples now match a hand trace of the spec, and the large files run in about two seconds each. The tiny case prints the required seven lines in the required order.

**What was wrong**, across the six files:

- **Projection order** in `proj.py` sorted the named columns instead of reporting them in the order named, with repeats. It also read every chunk of the column, even ones with no live row taking its value from them, and ignored the header and dictionary as cheaper sources of values.
- **Scheduling** in `pick.py` ordered whole conditions by their summed header estimate once, up front. The spec wants a per-pair choice, re-evaluated after every application, using the smaller of the chunk's live rows and the condition's count, with ties to earlier condition then lower chunk. It now runs a heap with lazy invalidation, so the wide shape stays fast.
- **Header bounds** in `hdr.py` ignored the `w` rounding. Bounds are now widened by G-1 on each side. The all-satisfy test for comparisons also required no nulls, which was missing.
- **Dictionaries** in `dct.py` were consulted even when a `*` token was present, and `rd` was printed on every consult rather than once per query per chunk.
- **Updates and deletions** in `step.py` were patched into the chunk values before counting, so the read counts were not "as written". Live rows with an update are now tested on the update alone, and chunks whose only live rows carry updates are never read.
- **Counts after a read** were only fixed for the condition being applied. A read now fixes the count of every condition of the query on that column and chunk.

`live.start`, `pick.run`, `live.rows` and `proj.run` keep their names and arguments. Wall time was about 2.1 seconds for the wide file and 0.4 seconds for the deep one, well inside the budget for the graded set.