"""A plain cycle stepper for the launch machine: no jumps, no frozen shortcut.

Two jobs. It is the naive-but-correct family the execution limit is meant to reject (it
advances one cycle at a time and only skips cycles in which no block is ready at all), and it
is an independent check on the sealed model's two exact shortcuts: every launch the model
runs, this runs too, and the printed lines must agree.

Hangs are found the only way a stepper can find them without reasoning about caches: an
all-spinning stretch is stepped and its full state (caches in fill order, rotations, every
spinner's registers) is remembered until one repeats.
"""
import sys

CMP = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b,
       "lt": lambda a, b: a < b, "ge": lambda a, b: a >= b}


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


def run(lines):
    cfg, labels, code = parse(lines)
    S, R, C = cfg["dev"]
    G = cfg["grid"]
    gm = dict(cfg["mem"])
    caches = [[] for _ in range(S)]          # list of [line, words] in fill order
    slots = [[None] * R for _ in range(S)]
    last = [R - 1] * S
    blk = [dict(pc=0, r=[0] * 8, outs=[], sm=None, slot=None, at=None, end=None, busy=0)
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

    def find(s, line):
        for i, (ln, _) in enumerate(caches[s]):
            if ln == line:
                return i
        return -1

    def load(s, cached, a):
        line, w = a // 4, a % 4
        i = find(s, line)
        if cached:
            if i >= 0:
                return caches[s][i][1][w]
            if len(caches[s]) >= C:
                caches[s].pop(0)
            words = [gm.get(4 * line + k, 0) for k in range(4)]
            caches[s].append([line, words])
            return words[w]
        if i >= 0:
            caches[s].pop(i)
        return gm.get(a, 0)

    def step(b, s):
        """Run one instruction; return True if it was a spin attempt that got through."""
        st = blk[b]
        f = code[st["pc"]]
        op = f[0]
        nxt_pc = st["pc"] + 1
        ok = False
        if op == "mov":
            st["r"][int(f[1][1:])] = get(b, f[2])
        elif op in ("add", "sub", "mul", "slt"):
            x, y = get(b, f[2]), get(b, f[3])
            st["r"][int(f[1][1:])] = {"add": x + y, "sub": x - y, "mul": x * y,
                                      "slt": int(x < y)}[op]
        elif op == "mod":
            st["r"][int(f[1][1:])] = get(b, f[2]) % int(f[3])
        elif op in ("ld.ca", "ld.cg"):
            st["r"][int(f[1][1:])] = load(s, op == "ld.ca", addr(b, f[2]))
        elif op == "st":
            a, v = addr(b, f[1]), get(b, f[2])
            gm[a] = v
            i = find(s, a // 4)
            if i >= 0:
                caches[s][i][1][a % 4] = v
        elif op == "atom.add":
            a, v = addr(b, f[2]), get(b, f[3])
            old = gm.get(a, 0)
            gm[a] = old + v
            st["r"][int(f[1][1:])] = old
        elif op == "fence":
            caches[s] = []
        elif op in ("spin.ca", "spin.cg"):
            a, want = addr(b, f[2]), get(b, f[4])
            got = load(s, op == "spin.ca", a)
            st["r"][int(f[1][1:])] = got
            if CMP[f[3]](got, want):
                ok = True
            else:
                nxt_pc = st["pc"]
        elif op == "work":
            st["busy"] = t + max(1, get(b, f[1]))
        elif op == "bra":
            nxt_pc = labels[f[1]]
        elif op in ("brz", "brnz"):
            if (get(b, f[1]) == 0) == (op == "brz"):
                nxt_pc = labels[f[2]]
        elif op == "out":
            st["outs"].append(get(b, f[1]))
        elif op == "exit":
            st["end"] = t
        st["pc"] = nxt_pc
        return ok

    freeing = []
    while True:
        for s, k in freeing:
            slots[s][k] = None
        freeing = []
        while nxt < G:
            free = [row.count(None) for row in slots]
            best = max(range(S), key=lambda s: (free[s], -s))
            if free[best] == 0:
                break
            k = slots[best].index(None)
            slots[best][k] = nxt
            blk[nxt].update(sm=best, slot=k, at=t)
            nxt += 1
        live = [b for row in slots for b in row if b is not None and blk[b]["end"] is None]
        if not live and nxt == G:
            break
        ready = [b for b in live if blk[b]["busy"] <= t]
        if not ready:
            t = min(blk[b]["busy"] for b in live)
            continue
        all_spin = len(ready) == len(live) and all(
            code[blk[b]["pc"]][0] in ("spin.ca", "spin.cg") for b in live)
        if all_spin:
            if phase is None:
                phase, seen = t, set()
            key = (tuple(tuple((ln, tuple(w)) for ln, w in c) for c in caches), tuple(last),
                   tuple((b, blk[b]["pc"], tuple(blk[b]["r"])) for b in live))
            if key in seen:
                hang = phase
                break
            seen.add(key)
        else:
            phase = None
        for s in range(S):
            for i in range(1, R + 1):
                k = (last[s] + i) % R
                b = slots[s][k]
                if b is not None and blk[b]["end"] is None and blk[b]["busy"] <= t:
                    last[s] = k
                    if step(b, s):
                        phase = None
                    if blk[b]["end"] is not None:
                        freeing.append((s, k))
                    break
        t += 1

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
                out.append("spin %d sm %d at %d on %d%s" % (
                    b, st["sm"], st["at"], addr(b, code[st["pc"]][2]),
                    "".join(" %d" % v for v in st["outs"])))
        out.append("left %d" % (G - nxt))
    for a in cfg["show"]:
        out.append("mem %d %d" % (a, gm.get(a, 0)))
    return out


if __name__ == "__main__":
    print("\n".join(run(open(sys.argv[1]).read().splitlines())))
