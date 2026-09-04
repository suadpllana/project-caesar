"""Does WHICH shortest script you use change where a note lands?
REF   = the pinned script (shortest, fewest groups, drop<add<keep)
KEEP  = a shortest script under the natural 'prefer keep' walk (what every
        textbook diff emits, and what difflib approximates)
DIFFL = difflib's own opcodes
"""
import difflib, random, sys
sys.path.insert(0, '/home/user/project-caesar/tasks/note-carry-forward/environment/app_src')
from scr import pin


def carried_ref(b, a):
    return pin.carried(b, a)


def carried_keepfirst(b, a):
    """Shortest, but the walk prefers keep, then drop, then add: the ordinary
    LCS backtrace. Same number of moves, different survivors."""
    n, m = len(b), len(a)
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            L[i][j] = L[i + 1][j + 1] + 1 if b[i] == a[j] else max(L[i + 1][j], L[i][j + 1])
    i = j = 0
    out = {}
    while i < n and j < m:
        if b[i] == a[j] and L[i][j] == L[i + 1][j + 1] + 1:
            out[i] = j; i += 1; j += 1
        elif L[i + 1][j] >= L[i][j + 1]:
            i += 1
        else:
            j += 1
    return out


def carried_difflib(b, a):
    out = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, b, a, autojunk=False).get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                out[i1 + d] = j1 + d
    return out


rng = random.Random(0)
tot = {"keep": 0, "diffl": 0}
N = int(sys.argv[1])
moved = 0
for _ in range(N):
    k = rng.randrange(2, 6)
    pool = ["ln%d" % i for i in range(k)]
    n = rng.randrange(6, 22)
    b = [rng.choice(pool) for _ in range(n)]
    a = list(b)
    for _ in range(rng.randrange(1, 5)):
        p = rng.randrange(max(1, len(a))); z = rng.randrange(3)
        if z == 0 and len(a) > 1: del a[p]
        elif z == 1: a.insert(p, rng.choice(pool))
        else: a[p] = rng.choice(pool)
    r = carried_ref(b, a)
    if r != carried_keepfirst(b, a): tot["keep"] += 1
    if r != carried_difflib(b, a): tot["diffl"] += 1
print("pairs %d" % N)
for name, c in tot.items():
    print("  survivors differ from the pinned script: %-6s %5d  (%.1f%%)" % (name, c, 100.0 * c / N))
