"""Every wrong reading of the board rule, measured against the reference."""
import difflib, random, sys
sys.path.insert(0, '/home/user/project-caesar/tasks/note-carry-forward/environment/app_src')
from scr import grp, pin


def _keep_pinned(b, a):
    return {i: j for kind, i, j in pin.reading(b, a, pin.script(b, a)) if kind == "K"}


def _keep_textbook(b, a):
    n, m = len(b), len(a)
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            L[i][j] = L[i+1][j+1] + 1 if b[i] == a[j] else max(L[i+1][j], L[i][j+1])
    i = j = 0; out = {}
    while i < n and j < m:
        if b[i] == a[j] and L[i][j] == L[i+1][j+1] + 1:
            out[i] = j; i += 1; j += 1
        elif L[i+1][j] >= L[i][j+1]: i += 1
        else: j += 1
    return out


def _keep_difflib(b, a):
    out = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, b, a, autojunk=False).get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1): out[i1 + d] = j1 + d
    return out


def run(revs, opens, mode="ref"):
    keepfn = {"textbook": _keep_textbook, "difflib": _keep_difflib}.get(mode, _keep_pinned)
    waiting = {}
    for at, nid, line in opens:
        waiting.setdefault(at, []).append((nid, line))
    log = []

    def settle(live):
        seen = {}; out = []
        for note in sorted(live, key=lambda n: n["id"]):
            owner = seen.get(note["line"])
            if owner is None or mode == "no-absorb":
                seen.setdefault(note["line"], note["id"]); out.append(note)
            elif mode == "absorb-newer":
                log.append(("absorb", note["id"], owner))
                out = [x for x in out if x["id"] != owner]; seen[note["line"]] = note["id"]; out.append(note)
            else:
                log.append(("absorb", owner, note["id"]))
        live[:] = sorted(out, key=lambda n: n["id"])

    if mode == "origin-to-head":                      # the composition shortcut
        live = []
        head = len(revs) - 1
        for at, nid, line in opens:
            keep = _keep_pinned(revs[at], revs[head])
            if line in keep: live.append({"id": nid, "line": keep[line]})
            else: log.append(("retire", nid))
        if head > 0:
            spans = grp.spans(revs[head - 1], revs[head])
            for note in live:
                if any(note["line"] in s for s in spans): log.append(("raise", note["id"]))
        settle(live)
        return sorted([(n["id"], n["line"]) for n in live]), log

    live = [{"id": n, "line": l} for n, l in waiting.get(0, [])]
    settle(live)
    for step in range(1, len(revs)):
        b, a = revs[step - 1], revs[step]
        keep = keepfn(b, a)
        spans = grp.spans(b, a)
        held = []
        for note in live:
            if note["line"] in keep:
                note["line"] = keep[note["line"]]; held.append(note)
            elif mode != "retire-silent":
                log.append(("retire", note["id"]))
        live = held
        for note in live:
            if mode == "raise-added-only":
                hit = any(note["line"] in s for s in spans) and note["line"] not in keep.values()
            else:
                hit = any(note["line"] in s for s in spans)
            if hit: log.append(("raise", note["id"]))
        for nid, line in waiting.get(step, []):
            live.append({"id": nid, "line": line})
        settle(live)
    return sorted([(n["id"], n["line"]) for n in live]), log


def gen(seed):
    rng = random.Random(seed)
    pool = ["ln%d" % i for i in range(rng.randrange(2, 7))]
    revs = [[rng.choice(pool) for _ in range(rng.randrange(8, 24))]]
    opens = []; nid = 0
    for step in range(rng.randrange(3, 8)):
        for _ in range(rng.randrange(0, 3)):
            if revs[-1]:
                opens.append((step, nid, rng.randrange(len(revs[-1])))); nid += 1
        nxt = list(revs[-1])
        for _ in range(rng.randrange(1, 5)):
            if not nxt: break
            p = rng.randrange(len(nxt)); z = rng.randrange(3)
            if z == 0 and len(nxt) > 1: del nxt[p]
            elif z == 1: nxt.insert(p, rng.choice(pool))
            else: nxt[p] = rng.choice(pool)
        revs.append(nxt)
    return revs, opens


if __name__ == "__main__":
    N = int(sys.argv[1])
    modes = ["origin-to-head", "textbook", "difflib", "raise-added-only",
             "absorb-newer", "no-absorb", "retire-silent"]
    hits = dict((m, 0) for m in modes)
    for s in range(N):
        revs, opens = gen(s)
        base = run(revs, opens, "ref")
        for m in modes:
            if run(revs, opens, m) != base: hits[m] += 1
    print("streams %d" % N)
    for m in modes:
        print("  %-18s moves %5d  (%.1f%%)" % (m, hits[m], 100.0 * hits[m] / N))
