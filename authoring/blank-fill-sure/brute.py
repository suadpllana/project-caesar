"""The definition, and nothing cleverer: try every filling and keep what every one returns.

Written from the rules alone, with its own reader, so that the model and the reference are
both checked against something that shares no code with either. It is exponential in the number
of labels by construction, so it only runs on small programs; `report` raises when a program
has more fillings than `limit`.
"""
import itertools
import re

INT = re.compile(r"(0|[1-9][0-9]*)$")
VAR = re.compile(r"[A-Z][A-Za-z0-9_]*$")


def const(tok):
    return int(tok) if INT.match(tok) else tok


def same(a, b):
    return type(a) is type(b) and a == b


def parse(lines):
    cols, rows, rules, asks = {}, {}, [], []
    for raw in lines:
        p = raw.split()
        if not p:
            continue
        if p[0] == "table":
            doms = []
            for d in p[2:]:
                if ".." in d:
                    lo, hi = d.split("..")
                    doms.append(set(range(int(lo), int(hi) + 1)) if int(hi) - int(lo) < 10000
                                else ("range", int(lo), int(hi)))
                else:
                    doms.append(set(d.split("|")))
            cols[p[1]] = doms
            rows[p[1]] = []
        elif p[0] == "row":
            rows[p[1]].append(tuple(v if v.startswith("?") else const(v) for v in p[2:]))
        elif p[0] == "rule":
            text = raw.split(None, 1)[1]
            head, body = text.split(":-")
            hp = head.split()
            items = re.findall(r"[a-z][a-z0-9_]*\([^)]*\)|[A-Z][A-Za-z0-9_]*\s*!=\s*[a-z0-9_]+", body)
            atoms, nots = [], []
            for it in items:
                if "!=" in it:
                    v, c = (s.strip() for s in it.split("!="))
                    nots.append((v, const(c)))
                else:
                    t, args = it.split("(", 1)
                    atoms.append((t, [a.strip() for a in args[:-1].split(",")]))
            rules.append((hp[0], hp[1:], atoms, nots))
            if hp[0] not in asks:
                asks.append(hp[0])
    return cols, rows, rules, asks


def allowed(cols, rows):
    out = {}
    for t, rs in rows.items():
        for r in rs:
            for d, v in zip(cols[t], r):
                if isinstance(v, str) and v.startswith("?"):
                    if isinstance(d, tuple):
                        raise RuntimeError("a label sits in a range too wide to enumerate")
                    out[v] = set(d) if v not in out else out[v] & d
    return out


def derive(rows, rule):
    q, head, atoms, nots = rule
    got = set()

    def walk(k, env):
        if k == len(atoms):
            for v, c in nots:
                if same(env[v], c):
                    return
            got.add(tuple(env[v] for v in head))
            return
        t, args = atoms[k]
        for r in rows[t]:
            e2 = dict(env)
            ok = True
            for a, x in zip(args, r):
                if a == "_":
                    continue
                if VAR.match(a):
                    if a in e2:
                        if not same(e2[a], x):
                            ok = False
                            break
                    else:
                        e2[a] = x
                elif not same(const(a), x):
                    ok = False
                    break
            if ok:
                walk(k + 1, e2)

    walk(0, {})
    return got


def key(row):
    return tuple((0, v, "") if type(v) is int else (1, 0, v) for v in row)


def report(lines, limit=400000):
    cols, rows, rules, asks = parse(lines)
    alw = allowed(cols, rows)
    labs = sorted(alw)
    total = 1
    for l in labs:
        total *= len(alw[l])
        if total > limit:
            raise RuntimeError("too many fillings")
    doms = [sorted(alw[l], key=lambda v: key((v,))) for l in labs]
    keep = None
    for combo in itertools.product(*doms):
        fill = dict(zip(labs, combo))
        filled = {t: [tuple(fill.get(v, v) if isinstance(v, str) and v.startswith("?") else v
                            for v in r) for r in rs] for t, rs in rows.items()}
        res = {q: set() for q in asks}
        for rule in rules:
            res[rule[0]] |= derive(filled, rule)
        if keep is None:
            keep = res
        else:
            for q in asks:
                keep[q] &= res[q]
    if keep is None:
        keep = {q: set() for q in asks}
    out = []
    for q in asks:
        rs = sorted(keep[q], key=key)
        out.append("ans %s %d" % (q, len(rs)))
        for r in rs:
            out.append(" ".join([q] + [str(v) for v in r]))
    return out
