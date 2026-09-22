"""Wrong readings of the machine, as switches on a plain stepper.

Each reading is a plausible misreading of one stated rule, the kind a solver keeps from its
prior or from the shipped engine. Running every reading over a generated population says how
often the population actually separates it from the model; a reading that moves nothing is a
reading the population is not shaped for (CLAUDE.md, 2026-09-09).

The same readings as file sets swapped into the reference - what tools/readingcheck.py
measures and what the cheats ship - are in readings.py.

Usage: python3 authoring/stale-line-spin/switches.py [seed ...]
"""
import sys
import collections

sys.path.insert(0, "tasks/stale-line-spin/tests/seal")
sys.path.insert(0, "tasks/stale-line-spin/tests")

CMP = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b,
       "lt": lambda a, b: a < b, "ge": lambda a, b: a >= b}

SWITCHES = {
    "coherent": "every load answers from global memory",
    "per-block-cache": "a cache per block, gone when the block exits",
    "store-broadcast": "a store updates every multiprocessor's cached copy",
    "atom-updates-own": "an atomic updates the issuer's cached copy",
    "lru": "a hit moves its line to the back of the replacement order",
    "cg-keeps": "a bypassing load leaves the cached line alone",
    "cg-drops-all": "a bypassing load drops the line from every multiprocessor's cache",
    "store-leaves-copy": "a store leaves the storer's own cached copy as it was",
    "fence-all": "a fence empties every multiprocessor's cache",
    "fence-noop": "a fence does nothing",
    "store-allocates": "a store that misses fills the line",
    "line-word": "a line is a single word",
    "place-mod": "block b goes to multiprocessor b mod S and waits for a slot there",
    "place-first-free": "a block goes to the lowest-numbered multiprocessor with a free slot",
    "free-same-cycle": "an exit frees its slot in the same cycle",
    "placed-next-cycle": "a placed block first issues on the next cycle",
    "rotate-from-zero": "each cycle the scan starts from slot 0",
    "sm-reverse": "multiprocessors issue in descending order",
    "work-plus-one": "a work of v cycles makes the block ready at t+v+1",
    "park-spinners": "a failing spinner leaves the rotation until its word is stored to",
    "skip-any-spin": "time is skipped whenever every ready block is failing a spin",
    "skip-no-rotate": "a skipped frozen stretch leaves every rotation where it was",
    "hang-no-store": "a hang is called as soon as every block spins and no attempt would pass",
    "hang-at-detect": "the hang is reported at the cycle it is detected",
    "lt-inclusive": "lt holds when the loaded value is at most v",
    "cmp-reversed": "a spin compares v against the loaded value",
}


def holds(sw, cmp, got, want):
    if "cmp-reversed" in sw:
        got, want = want, got
    if cmp == "lt" and "lt-inclusive" in sw:
        return got <= want
    return CMP[cmp](got, want)


def parse(lines):
    head, prog = [], None
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if prog is None:
            if s == "prog":
                prog = []
            else:
                head.append(s.split())
        else:
            prog.append(s)
    cfg = {"mem": {}, "show": []}
    for f in head:
        if f[0] == "dev":
            cfg["dev"] = [int(x) for x in f[1:]]
        elif f[0] == "grid":
            cfg["grid"] = int(f[1])
        elif f[0] == "mem":
            cfg["mem"][int(f[1])] = int(f[2])
        elif f[0] == "show":
            cfg["show"] += [int(x) for x in f[1:]]
    labels, code = {}, []
    for s in prog:
        if s.endswith(":"):
            labels[s[:-1]] = len(code)
        else:
            code.append(s.split())
    return cfg, labels, code


def run(lines, sw=frozenset(), cap=50_000):
    cfg, labels, code = parse(lines)
    S, R, C = cfg["dev"]
    G = cfg["grid"]
    LW = 1 if "line-word" in sw else 4
    gm = dict(cfg["mem"])
    per_block = "per-block-cache" in sw
    caches = [[] for _ in range(G if per_block else S)]
    slots = [[None] * R for _ in range(S)]
    last = [R - 1] * S
    blk = [dict(pc=0, r=[0] * 8, outs=[], sm=None, at=None, end=None, busy=0, parked=None)
           for _ in range(G)]
    nxt = 0
    t = 0
    hang = None
    phase = None
    seen = set()

    def get(b, tok):
        if tok == "%bid":
            return b
        if tok == "%sm":
            return blk[b]["sm"]
        if tok == "%nb":
            return G
        if tok.startswith("r"):
            return blk[b]["r"][int(tok[1:])]
        return int(tok)

    def addr(b, tok):
        body = tok[1:-1]
        if body.startswith("r"):
            if "+" in body:
                reg, k = body.split("+")
                return blk[b]["r"][int(reg[1:])] + int(k)
            return blk[b]["r"][int(body[1:])]
        return int(body)

    def cidx(b):
        return b if per_block else blk[b]["sm"]

    def find(ci, line):
        for i, (ln, _) in enumerate(caches[ci]):
            if ln == line:
                return i
        return -1

    def load(b, cached, a, dry=False):
        """Returns (value, changed)."""
        if "coherent" in sw:
            return gm.get(a, 0), False
        ci = cidx(b)
        line, w = a // LW, a % LW
        i = find(ci, line)
        if cached:
            if i >= 0:
                v = caches[ci][i][1][w]
                if "lru" in sw and not dry:
                    caches[ci].append(caches[ci].pop(i))
                return v, ("lru" in sw and i != len(caches[ci]) - 1)
            words = [gm.get(LW * line + k, 0) for k in range(LW)]
            if not dry:
                if len(caches[ci]) >= C:
                    caches[ci].pop(0)
                caches[ci].append([line, words])
            return words[w], True
        v = gm.get(a, 0)
        if "cg-drops-all" in sw and not dry:
            for cj in range(len(caches)):
                k2 = find(cj, line)
                if k2 >= 0:
                    caches[cj].pop(k2)
            return v, i >= 0
        if i >= 0 and "cg-keeps" not in sw:
            if not dry:
                caches[ci].pop(i)
            return v, True
        return v, False

    def wake_parked(a):
        for b in range(G):
            if blk[b]["parked"] == a:
                blk[b]["parked"] = None

    def step(b):
        st = blk[b]
        f = code[st["pc"]]
        op = f[0]
        nxt_pc = st["pc"] + 1
        res = "other"
        if op == "mov":
            st["r"][int(f[1][1:])] = get(b, f[2])
        elif op in ("add", "sub", "mul", "slt"):
            x, y = get(b, f[2]), get(b, f[3])
            st["r"][int(f[1][1:])] = {"add": x + y, "sub": x - y, "mul": x * y,
                                      "slt": int(x < y)}[op]
        elif op == "mod":
            st["r"][int(f[1][1:])] = get(b, f[2]) % int(f[3])
        elif op in ("ld.ca", "ld.cg"):
            st["r"][int(f[1][1:])] = load(b, op == "ld.ca", addr(b, f[2]))[0]
        elif op == "st":
            a, v = addr(b, f[1]), get(b, f[2])
            gm[a] = v
            targets = range(len(caches)) if "store-broadcast" in sw else [cidx(b)]
            for ci in targets:
                i = find(ci, a // LW)
                if i >= 0 and "store-leaves-copy" in sw:
                    pass
                elif i >= 0:
                    caches[ci][i][1][a % LW] = v
                elif ci == cidx(b) and "store-allocates" in sw:
                    load(b, True, a)
            wake_parked(a)
        elif op == "atom.add":
            a, v = addr(b, f[2]), get(b, f[3])
            old = gm.get(a, 0)
            gm[a] = old + v
            st["r"][int(f[1][1:])] = old
            if "atom-updates-own" in sw:
                i = find(cidx(b), a // LW)
                if i >= 0:
                    caches[cidx(b)][i][1][a % LW] = old + v
            wake_parked(a)
        elif op == "fence":
            if "fence-noop" in sw:
                pass
            elif "fence-all" in sw:
                for ci in range(len(caches)):
                    caches[ci] = []
            else:
                caches[cidx(b)] = []
        elif op in ("spin.ca", "spin.cg"):
            a, want = addr(b, f[2]), get(b, f[4])
            got, changed = load(b, op == "spin.ca", a)
            st["r"][int(f[1][1:])] = got
            if holds(sw, f[3], got, want):
                res = "success"
            else:
                nxt_pc = st["pc"]
                res = "moved" if changed else "quiet"
                if "park-spinners" in sw:
                    st["parked"] = a
        elif op == "work":
            st["busy"] = t + max(1, get(b, f[1])) + (1 if "work-plus-one" in sw else 0)
        elif op == "bra":
            nxt_pc = labels[f[1]]
        elif op in ("brz", "brnz"):
            if (get(b, f[1]) == 0) == (op == "brz"):
                nxt_pc = labels[f[2]]
        elif op == "out":
            st["outs"].append(get(b, f[1]))
        elif op == "exit":
            st["end"] = t
            if per_block:
                caches[b] = []
        st["pc"] = nxt_pc
        return res

    def ready(b):
        st = blk[b]
        return (b is not None and st["end"] is None and st["busy"] <= t
                and st["parked"] is None and not (
                    "placed-next-cycle" in sw and st["at"] == t))

    def would_pass(b):
        f = code[blk[b]["pc"]]
        a, want = addr(b, f[2]), get(b, f[4])
        got, changed = load(b, f[0] == "spin.ca", a, dry=True)
        return holds(sw, f[3], got, want), changed

    freeing = []
    steps = 0
    while True:
        for s, k in freeing:
            slots[s][k] = None
        freeing = []
        while nxt < G:
            free = [row.count(None) for row in slots]
            if "place-mod" in sw:
                best = nxt % S
            elif "place-first-free" in sw:
                cand = [s for s in range(S) if free[s]]
                best = cand[0] if cand else 0
            else:
                best = max(range(S), key=lambda s: (free[s], -s))
            if free[best] == 0:
                break
            k = slots[best].index(None)
            slots[best][k] = nxt
            blk[nxt].update(sm=best, at=t)
            nxt += 1
        live = [b for row in slots for b in row if b is not None and blk[b]["end"] is None]
        if not live and nxt == G:
            break
        spinning = [b for b in live if code[blk[b]["pc"]][0] in ("spin.ca", "spin.cg")]
        busy = [b for b in live if blk[b]["busy"] > t]
        if "park-spinners" in sw:
            active = [b for b in live if blk[b]["parked"] is None]
            if not active:
                hang = t
                break
        all_spin = len(spinning) == len(live) and not busy
        if all_spin:
            if phase is None:
                phase, seen = t, set()
            if "hang-no-store" in sw and all(not would_pass(b)[0] for b in spinning):
                hang = phase
                break
            key = (tuple(tuple((ln, tuple(w)) for ln, w in c) for c in caches), tuple(last),
                   tuple((b, blk[b]["pc"]) for b in live))
            if key in seen:
                hang = t if "hang-at-detect" in sw else phase
                break
            seen.add(key)
        else:
            phase = None
        ready_now = [b for b in live if ready(b)]
        if not ready_now and "placed-next-cycle" in sw and any(
                blk[b]["at"] == t for b in live):
            t += 1
            continue
        if not ready_now:
            wakes = [blk[b]["busy"] for b in live if blk[b]["busy"] > t]
            if not wakes:
                hang = t
                break
            t = min(wakes)
            continue
        if ("skip-no-rotate" in sw and busy and ready_now and
                all(code[blk[b]["pc"]][0] in ("spin.ca", "spin.cg") and not would_pass(b)[0]
                    and not would_pass(b)[1] for b in ready_now)):
            t = min(blk[b]["busy"] for b in busy)
            continue
        if ("skip-any-spin" in sw and busy and
                all(code[blk[b]["pc"]][0] in ("spin.ca", "spin.cg") and not would_pass(b)[0]
                    for b in ready_now)):
            until = min(blk[b]["busy"] for b in busy)
            for s in range(S):
                rs = [k for k in range(R) if slots[s][k] is not None and ready(slots[s][k])]
                if rs:
                    order = sorted(rs, key=lambda k: (k - last[s] - 1) % R)
                    last[s] = order[(until - t - 1) % len(order)]
            t = until
            continue
        order_sm = range(S - 1, -1, -1) if "sm-reverse" in sw else range(S)
        for s in order_sm:
            start = -1 if "rotate-from-zero" in sw else last[s]
            for i in range(1, R + 1):
                k = (start + i) % R
                b = slots[s][k]
                if b is not None and ready(b):
                    last[s] = k
                    if step(b) == "success":
                        phase = None
                    if blk[b]["end"] is not None:
                        if "free-same-cycle" in sw:
                            slots[s][k] = None
                        else:
                            freeing.append((s, k))
                    break
        t += 1
        steps += 1
        if steps > cap:
            return ["cap"]
        if "free-same-cycle" in sw:
            while nxt < G:
                free = [row.count(None) for row in slots]
                best = max(range(S), key=lambda s: (free[s], -s))
                if free[best] == 0:
                    break
                k = slots[best].index(None)
                slots[best][k] = nxt
                blk[nxt].update(sm=best, at=t - 1)
                nxt += 1

    out = []
    for b in range(G):
        st = blk[b]
        if st["end"] is not None:
            out.append("blk %d sm %d at %d end %d%s" % (
                b, st["sm"], st["at"], st["end"], "".join(" %d" % v for v in st["outs"])))
    if hang is not None:
        out.append("hang %d" % hang)
        for b in range(G):
            st = blk[b]
            if st["at"] is not None and st["end"] is None:
                f = code[st["pc"]]
                where = addr(b, f[2]) if f[0].startswith("spin") else -1
                out.append("spin %d sm %d at %d on %d%s" % (
                    b, st["sm"], st["at"], where, "".join(" %d" % v for v in st["outs"])))
        out.append("left %d" % (G - nxt))
    for a in cfg["show"]:
        out.append("mem %d %d" % (a, gm.get(a, 0)))
    return out


def main(seeds):
    import gen
    import model
    per = 40
    moved = collections.defaultdict(collections.Counter)
    total = collections.Counter()
    for seed in seeds:
        for fam, name, lines in gen.programs(seed, per):
            if fam in ("wide", "deep"):
                continue
            want = model.expect(lines)
            base = run(lines)
            assert base == want, ("switchless stepper disagrees with the model", name)
            total[fam] += 1
            for rd in SWITCHES:
                if run(lines, frozenset([rd])) != want:
                    moved[rd][fam] += 1
    fams = sorted(total)
    print("%-18s %s   all" % ("reading", " ".join("%7s" % f for f in fams)))
    for rd in SWITCHES:
        row = ["%6.1f%%" % (100.0 * moved[rd][f] / total[f]) for f in fams]
        allp = 100.0 * sum(moved[rd].values()) / sum(total.values())
        print("%-18s %s %5.1f%%" % (rd, " ".join(row), allp))


if __name__ == "__main__":
    main(sys.argv[1:] or ["r1"])
