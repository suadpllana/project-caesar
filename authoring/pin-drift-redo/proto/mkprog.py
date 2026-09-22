"""Random well-formed programs, for differential testing of the two engines."""
import random


def prog(seed, keys=5, ops=40, txs=3, marky=True):
    r = random.Random(seed)
    lines = ["cfg %d" % keys]
    live = []
    nxt = 1
    opened = 0
    body = []
    while len(body) < ops:
        if not live or (len(live) < txs and r.random() < 0.25):
            live.append(nxt)
            body.append("tx %d" % nxt)
            nxt += 1
            opened += 1
            continue
        t = r.choice(live)
        pick = r.random()
        k = r.randrange(keys)
        if pick < 0.14:
            body.append("rd %d %d" % (t, k))
        elif pick < 0.30:
            body.append("add %d %d %d" % (t, k, r.randint(-9, 9)))
        elif pick < 0.40:
            body.append("put %d %d %d" % (t, k, r.randint(0, 40)))
        elif pick < 0.50:
            body.append("cpy %d %d %d" % (t, k, r.randrange(keys)))
        elif pick < 0.56:
            body.append("raw %d %d %d" % (t, k, r.randrange(keys)))
        elif pick < 0.60:
            lo = r.randrange(keys)
            body.append("bmp %d %d %d %d" % (t, lo, r.randint(lo + 1, keys), r.randint(-6, 6)))
        elif pick < 0.64 and marky:
            body.append("chk %d %d %d" % (t, k, r.randint(0, 12)))
        elif pick < 0.68 and marky:
            body.append("lim %d %d %d" % (t, k, r.randint(-4, 12)))
        elif pick < 0.78 and marky:
            body.append("mk %d" % t)
        elif pick < 0.84 and marky:
            body.append("un %d" % t)
        elif pick < 0.88:
            body.append("drp %d" % t)
            live.remove(t)
        else:
            body.append("fin %d" % t)
            live.remove(t)
    for t in live:
        body.append("fin %d" % t)
    return "\n".join(lines + body) + "\n"
