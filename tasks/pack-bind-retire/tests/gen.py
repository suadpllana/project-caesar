"""Case generation.

Every collection is sorted before it is sampled from and no set is ever iterated, so the
same seed builds the same case in any process whatever PYTHONHASHSEED is. Needs only ever
point at an earlier pack, which keeps the needs graph acyclic without a check.

The shapes the graded set has to contain, and which are forced rather than hoped for: a pack
dropped and loaded again while a resident that needs it is still standing, a use that reaches
a resident nothing has standing any more, a weak name whose only provider has gone, and a
chain that walks out of one resident into another.
"""
import argparse
import os
import random

PACKS = ("aa", "bb", "cc", "dd", "ee", "ff", "gg")
NAMES = ("n1", "n2", "n3", "n4")


def declare(rg, packs, names):
    dec = {}
    for i, p in enumerate(packs):
        pv = sorted(rg.sample(names, rg.randint(1, min(2, len(names)))))
        rq = sorted(rg.sample(names, rg.randint(0, 2)))
        spare = sorted(x for x in names if x not in rq)
        wk = sorted(rg.sample(spare, 1)) if spare and rg.random() < 0.55 else []
        earlier = sorted(packs[:i])
        nd = []
        if earlier:
            deep = sorted(earlier, key=lambda x: (-len(dec[x]["nd"]), x))
            if rg.random() < 0.65:
                nd.append(deep[0])
            for x in sorted(rg.sample(earlier, rg.randint(0, min(2, len(earlier))))):
                if x not in nd:
                    nd.append(x)
            nd = nd[:2]
        pool = sorted(rq + wk)
        st = sorted(rg.sample(pool, rg.randint(0, min(2, len(pool))))) if pool and rg.random() < 0.7 else []
        dec[p] = {"pv": pv, "rq": rq, "wk": wk, "nd": nd, "st": st}
    return dec


def sharpen(dec, packs):
    for p in packs:
        picked = None
        for q in dec[p]["nd"]:
            picked = q
            break
        if picked is None:
            continue
        if "n8" not in dec[p]["pv"]:
            dec[p]["pv"].append("n8")
        if "n8" not in dec[picked]["rq"]:
            dec[picked]["rq"].append("n8")
        if "n8" not in dec[picked]["st"]:
            dec[picked]["st"].append("n8")
        break
    for p in packs:
        nd = dec[p]["nd"]
        if len(nd) < 2 or not dec[nd[0]]["nd"]:
            continue
        d = dec[nd[0]]["nd"][0]
        c = nd[1]
        if d == c:
            continue
        for x in (c, d):
            if "n9" not in dec[x]["pv"]:
                dec[x]["pv"].append("n9")
        if "n9" not in dec[p]["rq"]:
            dec[p]["rq"].append("n9")
        break
    return dec


def closure(dec, p):
    out = []
    q = [p]
    while q:
        x = q.pop(0)
        if x in out:
            continue
        out.append(x)
        q.extend(dec[x]["nd"])
    return out


def script(rg, dec, packs, names):
    evs = []
    standing = []
    opened = []

    def load(p, md):
        evs.append("ld %s %s" % (p, md))
        for x in closure(dec, p):
            if x not in standing:
                standing.append(x)
        if md == "open" and p not in opened:
            opened.append(p)

    def drop(p):
        evs.append("dp %s" % p)
        if p in standing:
            standing.remove(p)
        if p in opened:
            opened.remove(p)

    def use(p, hops):
        evs.append("us %s %s" % (p, " ".join(hops)))

    def wants(p):
        return sorted(set(dec[p]["rq"] + dec[p]["wk"]))

    load(rg.choice(sorted(packs)), "open" if rg.random() < 0.6 else "own")
    for _ in range(rg.randint(6, 12)):
        k = rg.random()
        if k < 0.30 or not standing:
            load(rg.choice(sorted(packs)), "open" if rg.random() < 0.55 else "own")
        elif k < 0.72:
            live = [p for p in standing if wants(p)]
            if not live:
                continue
            p = rg.choice(sorted(live))
            hops = [rg.choice(wants(p))]
            if rg.random() < 0.4:
                hops.append(rg.choice(sorted(names)))
            use(p, hops)
        else:
            drop(rg.choice(sorted(packs)))

    quiet = [p for p in standing if p not in opened]
    if quiet:
        p = rg.choice(sorted(quiet))
        load(p, "open")
        for q in sorted(standing):
            if wants(q):
                use(q, [rg.choice(wants(q))])

    swap = None
    for p in sorted(packs):
        if [q for q in standing if p in dec[q]["nd"]]:
            swap = p
            break
    if swap is None and standing:
        swap = rg.choice(sorted(standing))
    if swap is not None:
        drop(swap)
        for q in sorted(standing):
            for nm in wants(q):
                if nm in dec[swap]["pv"]:
                    use(q, [nm])
        load(swap, "open" if rg.random() < 0.7 else "own")
        for q in sorted(standing):
            for nm in wants(q):
                if nm in dec[swap]["pv"]:
                    use(q, [nm])
            if wants(q) and rg.random() < 0.5:
                use(q, [rg.choice(wants(q)), rg.choice(sorted(names))])

    for q in sorted(standing):
        for nm in wants(q)[:3]:
            use(q, [nm])

    tail = sorted(standing)
    rg.shuffle(tail)
    for p in tail[: rg.randint(1, max(1, len(tail)))]:
        drop(p)
        for q in sorted(standing):
            if wants(q):
                use(q, [rg.choice(wants(q))])
    return evs


def spec(seed):
    rg = random.Random(seed)
    packs = list(PACKS[: rg.randint(5, 7)])
    names = list(NAMES[: rg.randint(3, 4)])
    dec = sharpen(declare(rg, packs, names), packs)
    lines = []
    for p in packs:
        lines.append("pk %s" % p)
        for t in ("pv", "rq", "wk", "nd", "st"):
            for v in dec[p][t]:
                lines.append("%s %s" % (t, v))
    lines.extend(script(rg, dec, packs, names))
    return "\n".join(lines) + "\n"


def build(nonce, count, into):
    os.makedirs(into, exist_ok=True)
    out = []
    for i in range(count):
        seed = int(nonce[:16], 16) ^ (i * 0x9E3779B1)
        name = "g%03d" % i
        path = os.path.join(into, name + ".txt")
        with open(path, "w", encoding="ascii") as fh:
            fh.write(spec(seed))
        out.append(name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nonce", required=True)
    ap.add_argument("--count", type=int, default=300)
    ap.add_argument("--into", required=True)
    a = ap.parse_args()
    build(a.nonce, a.count, a.into)


if __name__ == "__main__":
    main()
