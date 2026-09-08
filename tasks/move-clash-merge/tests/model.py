"""Independent implementation of the whole run, written from the stated rules.

Written apart from the reference under /app: a tree here is a flat dict of tuples with no
child index, paths are recomputed on demand, folder survival is an upward walk per node
rather than a fixed point over the whole set, and loops are found by colouring rather than
by following a trail. The greedy emission is fixed by the rules and is the same procedure
in both, which is stated rather than claimed away.

Layout of a tree: {key: (kind, parent, name, content)}; ROOT is always present.

The sections below follow the rules in the brief:
  parse/apply   the scenario language, and each side's own rules for applying it
  survive       which nodes the record keeps
  settle        folder and name per node, the walk up, the loop break
  hold/number   contents, the second node a two-sided write leaves, and the numbering
  contest       the case-blind name contests and the marks
  emit          the operations a side can carry out, in order
  replay        the driver: rounds, printing, re-keying by path
"""

ROOT = "0"


def new():
    return {ROOT: ("d", None, "", None)}


def pth(t, k):
    out = []
    while k != ROOT:
        kind, par, nm, c = t[k]
        out.append(nm)
        k = par
    return "/" + "/".join(reversed(out)) if out else "/"


def kids(t, k):
    return [j for j in t if j != ROOT and t[j][1] == k]


def at(t, path):
    if path == "/":
        return ROOT
    k = ROOT
    for part in path.strip("/").split("/"):
        nxt = None
        for j in kids(t, k):
            if t[j][2] == part:
                nxt = j
                break
        if nxt is None:
            return None
        k = nxt
    return k


def taken(t, par, nm, fold):
    for j in kids(t, par):
        got = t[j][2]
        if got == nm or (fold and got.lower() == nm.lower()):
            return True
    return False


def inside(t, k, other):
    while k is not None:
        if k == other:
            return True
        k = t[k][1] if k in t else None
    return False


def cut(path):
    i = path.rfind("/")
    return (path[:i] or "/"), path[i + 1:]


def glue(par, nm):
    return ("/" if par == "/" else par + "/") + nm


# ---------------------------------------------------------------- scenario language

def parse(lines):
    base = new()
    top = 0
    rounds = []
    lo, ro = [], []
    for raw in lines:
        w = raw.split()
        if not w:
            continue
        if w[0] in ("d", "f"):
            par, nm = cut(w[2])
            base[w[1]] = (w[0], at(base, par), nm, w[3] if w[0] == "f" else None)
            top = max(top, int(w[1]))
        elif w[0] == "sync":
            rounds.append((lo, ro))
            lo, ro = [], []
        elif w[0] == "L":
            lo.append(tuple(w[1:]))
        elif w[0] == "R":
            ro.append(tuple(w[1:]))
    if lo or ro:
        rounds.append((lo, ro))
    return base, top + 1, rounds


def do(t, op, fold, fresh):
    kind = op[0]
    if kind in ("mkd", "mkf"):
        par, nm = cut(op[1])
        if op[1] == "/" or not nm:
            return
        pk = at(t, par)
        if pk is None or t[pk][0] != "d" or taken(t, pk, nm, fold):
            return
        t[fresh()] = ("d" if kind == "mkd" else "f", pk, nm,
                      None if kind == "mkd" else op[2])
    elif kind == "ed":
        k = at(t, op[1])
        if k is not None and k != ROOT and t[k][0] == "f":
            t[k] = (t[k][0], t[k][1], t[k][2], op[2])
    elif kind == "rm":
        k = at(t, op[1])
        if k is not None and k != ROOT and not kids(t, k):
            del t[k]
    elif kind == "mv":
        k = at(t, op[1])
        if k is None or k == ROOT or op[1] == op[2] or op[2] == "/":
            return
        par, nm = cut(op[2])
        if not nm:
            return
        pk = at(t, par)
        if pk is None or t[pk][0] != "d" or taken(t, pk, nm, fold):
            return
        if inside(t, pk, k):
            return
        t[k] = (t[k][0], pk, nm, t[k][3])


# ---------------------------------------------------------------- the merge

def tag(rec, side, key):
    return key if key in rec else side + ":" + key


def one_axis(av, lv, rv, hl, hr):
    if hl and hr:
        if lv == rv:
            return lv, ("a" if lv == av else "R")
        if lv == av:
            return rv, "R"
        if rv == av:
            return lv, "L"
        return rv, "R"
    if hl:
        return lv, ("a" if lv == av else "L")
    return rv, ("a" if rv == av else "R")


def where(rec, lo, ro):
    raw = {}
    for key in rec:
        if key == ROOT:
            continue
        hl, hr = key in lo, key in ro
        if not hl and not hr:
            continue
        ak, ap, an, ac = rec[key]
        lp = tag(rec, "L", lo[key][1]) if hl else None
        rp = tag(rec, "R", ro[key][1]) if hr else None
        par, ps = one_axis(ap, lp, rp, hl, hr)
        nm, ns = one_axis(an, lo[key][2] if hl else None,
                          ro[key][2] if hr else None, hl, hr)
        raw[key] = (par, nm, ps, ns)
    for side, t in (("L", lo), ("R", ro)):
        for key in t:
            if key == ROOT or key in rec:
                continue
            raw[side + ":" + key] = (tag(rec, side, t[key][1]), t[key][2], side, side)
    return raw


def survive(rec, lo, ro, raw):
    alive = set()
    for key in rec:
        if key == ROOT:
            continue
        hl, hr = key in lo, key in ro
        if hl and hr:
            alive.add(key)
        elif hl or hr:
            side, t = ("L", lo) if hl else ("R", ro)
            kind, par, nm, c = t[key]
            if tag(rec, side, par) != rec[key][1] or nm != rec[key][2] or c != rec[key][3]:
                alive.add(key)
    grown = set(alive)
    for key in alive:
        walk = key
        while walk in rec and raw.get(walk, (None,))[0] == rec[walk][1]:
            par = rec[walk][1]
            if par == ROOT or par in grown:
                break
            grown.add(par)
            walk = par
    for side, t in (("L", lo), ("R", ro)):
        for key in t:
            if key != ROOT and key not in rec:
                grown.add(side + ":" + key)
    return grown


def upward(rec, alive, par):
    while par != ROOT and par not in alive:
        par = rec[par][1]
    return par


def ring(place):
    colour = {}
    for start in place:
        if colour.get(start):
            continue
        chain = []
        node = start
        while node in place and colour.get(node) is None:
            colour[node] = 1
            chain.append(node)
            node = place[node][0]
        if colour.get(node) == 1 and node in place:
            cycle = chain[chain.index(node):]
            for k in chain:
                colour[k] = 2
            return cycle
        for k in chain:
            colour[k] = 2
    return None


def small(key):
    try:
        return (0, int(key))
    except ValueError:
        return (1, key)


def settle(rec, alive, raw):
    place = {}
    for key, (par, nm, ps, ns) in raw.items():
        if key in alive:
            place[key] = (upward(rec, alive, par), nm, ps, ns)
    stuck = set()
    while True:
        loop = ring(place)
        if not loop:
            return place
        pool = [k for k in loop if k not in stuck and place[k][2] == "L"]
        if not pool:
            pool = [k for k in loop if k not in stuck]
        if not pool:
            return place
        who = min(pool, key=small)
        par, nm, ps, ns = place[who]
        back = rec[who][1] if who in rec else ROOT
        place[who] = (upward(rec, alive, back), nm, "a", ns)
        stuck.add(who)


def hold(rec, lo, ro, place):
    body = {}
    twins = []
    for key in place:
        if key in rec:
            kind, ap, an, ac = rec[key]
            if kind == "d":
                body[key] = None
                continue
            hl, hr = key in lo, key in ro
            lc = lo[key][3] if hl else None
            rc = ro[key][3] if hr else None
            if hl and hr:
                if lc == rc:
                    body[key] = lc
                elif rc == ac:
                    body[key] = lc
                elif lc == ac:
                    body[key] = rc
                else:
                    body[key] = lc
                    twins.append(key)
            else:
                body[key] = lc if hl else rc
        else:
            side, k = key.split(":", 1)
            body[key] = (lo if side == "L" else ro)[k][3]
    return body, sorted(twins, key=small)


def number(rec, lo, ro, place, twins, nxt):
    ids = dict((k, k) for k in place if k in rec)
    queue = []
    for side, t in (("R", ro), ("L", lo)):
        queue += [key for _, key in sorted(
            (pth(t, k), side + ":" + k) for k in t if k != ROOT and k not in rec)]
    queue += ["C:" + k for k in twins]
    for key in queue:
        if key in place:
            ids[key] = str(nxt)
            nxt += 1
    return ids, nxt


def kept_name(rec, key, par, nm):
    return key in rec and rec[key][1] == par and rec[key][2] == nm


def on_side(rec, t, side, key, nm):
    if key.startswith(side + ":"):
        return t[key.split(":", 1)[1]][2].lower() == nm.lower()
    if key in rec and key in t:
        return t[key][2].lower() == nm.lower()
    return False


def contest(rec, lo, ro, place, ids):
    final = {}
    folders = {}
    for key in place:
        folders.setdefault(place[key][0], []).append(key)
    for par, members in folders.items():
        by = {}
        for key in members:
            by.setdefault(place[key][1].lower(), []).append(key)
        used = set()
        beaten = []
        for low, group in by.items():
            if len(group) == 1:
                final[group[0]] = place[group[0]][1]
                used.add(low)
                continue
            best, score = None, None
            for key in group:
                nm = place[key][1]
                if key.startswith("C:"):
                    rank = 4
                elif kept_name(rec, key, par, nm):
                    rank = 0
                elif on_side(rec, ro, "R", key, nm):
                    rank = 1
                elif on_side(rec, lo, "L", key, nm):
                    rank = 2
                else:
                    rank = 3
                got = (rank, int(ids[key]))
                if score is None or got < score:
                    best, score = key, got
            final[best] = place[best][1]
            used.add(final[best].lower())
            beaten += [k for k in group if k != best]
        for key in sorted(beaten, key=lambda k: int(ids[k])):
            nm = place[key][1]
            dot = nm.rfind(".")
            i = 1
            while True:
                if 0 < dot < len(nm) - 1:
                    cand = "%s~%d%s" % (nm[:dot], i, nm[dot:])
                else:
                    cand = "%s~%d" % (nm, i)
                if cand.lower() not in used:
                    break
                i += 1
            final[key] = cand
            used.add(cand.lower())
    return final


def species(rec, lo, ro, key):
    if key.startswith("C:"):
        return "f"
    if key in rec:
        return rec[key][0]
    side, k = key.split(":", 1)
    return (lo if side == "L" else ro)[k][0]


def merge(rec, nxt, lo, ro):
    raw = where(rec, lo, ro)
    alive = survive(rec, lo, ro, raw)
    place = settle(rec, alive, raw)
    body, twins = hold(rec, lo, ro, place)
    for key in twins:
        place["C:" + key] = (place[key][0], place[key][1], "c", "c")
        body["C:" + key] = ro[key][3]
    ids, nxt2 = number(rec, lo, ro, place, twins, nxt)
    final = contest(rec, lo, ro, place, ids)
    tgt = new()
    left = list(place)
    while left:
        again = []
        for key in left:
            par = place[key][0]
            pk = ROOT if par == ROOT else ids.get(par)
            if pk is None or pk not in tgt:
                again.append(key)
                continue
            tgt[ids[key]] = (species(rec, lo, ro, key), pk, final[key], body[key])
        if len(again) == len(left):
            break
        left = again
    maps = []
    for side, t in (("L", lo), ("R", ro)):
        m = {ROOT: ROOT}
        for key in t:
            if key == ROOT:
                continue
            got = ids.get(tag(rec, side, key))
            if got is not None and got in tgt:
                m[key] = got
        maps.append(m)
    return tgt, nxt2, maps[0], maps[1]


# ---------------------------------------------------------------- emitting operations

ORDER = {"rm": 0, "mv": 1, "mkd": 2, "mkf": 2, "ed": 3}
CEILING = 4000


def anchor(tgt, inv, tk):
    par = tgt[tk][1]
    return ROOT if par == ROOT else inv.get(par)


def offers(work, tgt, m, inv, fold):
    out = []
    for ck in work:
        if ck != ROOT and ck not in m and not kids(work, ck):
            out.append((("rm", pth(work, ck)), None))
    for ck, tk in m.items():
        if ck == ROOT:
            continue
        kind, par, nm, c = work[ck]
        tkind, tpar, tnm, tc = tgt[tk]
        want = anchor(tgt, inv, tk)
        if par == want and nm == tnm:
            if tkind == "f" and c != tc:
                out.append((("ed", pth(work, ck), tc), None))
            continue
        if want is None or want not in work:
            continue
        if inside(work, want, ck) or taken(work, want, tnm, fold):
            continue
        out.append((("mv", pth(work, ck), glue(pth(work, want), tnm)), None))
    for tk in tgt:
        if tk == ROOT or tk in inv:
            continue
        tkind, tpar, tnm, tc = tgt[tk]
        want = anchor(tgt, inv, tk)
        if want is None or want not in work or taken(work, want, tnm, fold):
            continue
        dst = glue(pth(work, want), tnm)
        out.append((("mkd", dst) if tkind == "d" else ("mkf", dst, tc), tk))
    return out


def shove(work, tgt, inv, fold):
    pick = None
    for tk in tgt:
        if tk == ROOT:
            continue
        want = anchor(tgt, inv, tk)
        if want is None or want not in work:
            continue
        ck = inv.get(tk)
        if ck is not None and work[ck][1] == want and work[ck][2] == tgt[tk][2]:
            continue
        for other in kids(work, want):
            got = work[other][2]
            if got == tgt[tk][2] or (fold and got.lower() == tgt[tk][2].lower()):
                cand = (small(tk), pth(work, other))
                if pick is None or cand < pick:
                    pick = cand
    if pick is None:
        return None
    here = pick[1]
    ck = at(work, here)
    par = work[ck][1]
    i = 1
    while taken(work, par, "~t%d" % i, fold):
        i += 1
    return ("mv", here, glue(pth(work, par), "~t%d" % i))


def emit(cur, tgt, m, fold):
    work = dict(cur)
    m = dict((k, v) for k, v in m.items() if k in work)
    inv = dict((v, k) for k, v in m.items())
    ops = []
    made = [0]

    def fresh():
        made[0] += 1
        return "e%d" % made[0]

    for _ in range(CEILING):
        best = None
        for op, tk in offers(work, tgt, m, inv, fold):
            key = (ORDER[op[0]], op[1])
            if best is None or key < best[0]:
                best = (key, op, tk)
        if best is None:
            op = shove(work, tgt, inv, fold)
            if op is None:
                return ops
            ops.append(op)
            do(work, op, fold, fresh)
            continue
        ops.append(best[1])
        if best[2] is None:
            do(work, best[1], fold, fresh)
        else:
            tk = best[2]
            par, nm = cut(best[1][1])
            pk = at(work, par)
            work["t:" + tk] = (tgt[tk][0], pk, nm, tgt[tk][3])
            m["t:" + tk] = tk
            inv[tk] = "t:" + tk
    return ops


# ---------------------------------------------------------------- the driver

def rekey(cur, tgt, fresh):
    out = new()
    seen = {}
    for path, key in sorted((pth(cur, k), k) for k in cur if k != ROOT):
        par, nm = cut(path)
        pk = seen[par] if par != "/" else ROOT
        kind, _, _, c = cur[key]
        tk = at(tgt, path)
        if tk is None or tgt[tk][0] != kind:
            tk = fresh()
        out[tk] = (kind, pk, nm, c)
        seen[path] = tk
    return out


def replay(text):
    base, nxt, rounds = parse(text.split("\n"))
    rec = dict(base)
    lo, ro = dict(base), dict(base)
    made = [0]

    def fresh():
        made[0] += 1
        return "w%d" % made[0]

    out = []
    for i, (lops, rops) in enumerate(rounds, 1):
        for op in lops:
            do(lo, op, False, fresh)
        for op in rops:
            do(ro, op, True, fresh)
        tgt, nxt, ml, mr = merge(rec, nxt, lo, ro)
        for label, cur, m, fold in (("L", lo, ml, False), ("R", ro, mr, True)):
            for op in emit(cur, tgt, m, fold):
                out.append("%d %s %s" % (i, label, " ".join(op)))
                do(cur, op, fold, fresh)
        lo = rekey(lo, tgt, fresh)
        ro = rekey(ro, tgt, fresh)
        for label, cur in (("l", lo), ("r", ro)):
            for path, key in sorted((pth(cur, k), k) for k in cur if k != ROOT):
                kind, par, nm, c = cur[key]
                out.append("%d %s %s %s" % (i, label, path, c if kind == "f" else "-"))
        rec = tgt
    return out
