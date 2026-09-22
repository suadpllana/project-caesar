"""Lower bound on the per-row replay audit at the deep scale. Authoring only.

A correct replay audit has to compute, for every row, the removed set of a lone delete, plus
clearing and refusal. This measures only the removed-set part, written as tightly as Python
allows: integer ids, flat lists, one precomputed list of referrers per row, a counter array
reset through a touched list, match sets shared rather than copied. Anything that replays a
delete per row does at least this much work, so its extrapolated time is a floor for the whole
naive family, not an estimate of a typical one.

    python -u time_naive.py <deep scripts> <sampled rows per script>
"""
import random
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import agree  # noqa: E402,F401  (puts the sealed directory on the path)
import gen  # noqa: E402
import model  # noqa: E402


def floor(text, sample, rng):
    db = model.DB(text)
    data = {t: dict(r) for t, r in db.data.items()}
    ix = model.Index(db, data)
    rows = [(t, rid) for t in db.order for rid in sorted(data[t])]
    node = {r: i for i, r in enumerate(rows)}
    n = len(rows)
    kids = [[] for _ in range(n)]
    need = [0] * n
    for v, (t, rid) in enumerate(rows):
        vals = data[t][rid]
        for r in db.out_refs[t]:
            if r["act"] != "cascade":
                continue
            pat = model.shape(r, vals)
            if not pat:
                continue
            ms = ix.parents(r, pat, vals)
            if not ms:
                continue
            need[v] = len(ms)
            for p in ms:
                kids[node[(r["ktab"], p)]].append(v)
            break
    picks = rng.sample(range(n), sample)
    cnt = [0] * n
    t0 = time.perf_counter()
    total = 0
    for r in picks:
        touched = []
        stack = [r]
        removed = 1
        while stack:
            p = stack.pop()
            for c in kids[p]:
                k = cnt[c]
                if k == 0:
                    touched.append(c)
                k += 1
                cnt[c] = k
                if k == need[c] and c != r:
                    removed += 1
                    stack.append(c)
        for c in touched:
            cnt[c] = 0
        total += removed
    el = time.perf_counter() - t0
    return n, el / sample, total / sample


def main():
    scripts, sample = int(sys.argv[1]), int(sys.argv[2])
    grand = 0.0
    for i in range(scripts):
        rng = random.Random("floor:%d" % i)
        text = gen.deep(rng)
        audits = sum(1 for line in text.splitlines() if line == "audit")
        n, per, mean = floor(text, sample, rng)
        est = per * n * audits
        grand += est
        print("deep-%d rows %d mean removed %.0f  floor per row %.3f ms  x %d rows x %d audits"
              " = %.0f s" % (i, n, mean, per * 1000, n, audits, est), flush=True)
    print("floor for the %d deep scripts: %.0f s" % (scripts, grand))


if __name__ == "__main__":
    main()
