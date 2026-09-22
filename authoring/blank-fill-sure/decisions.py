"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The graded decision is
whether a candidate row - one the query returns under at least one filling - is in the report.
Every feature is raw: counted off the program text and a join that lets a placeholder match any
value its columns allow, before any reasoning about fillings. Nothing derived is offered - no
count of unused values, no classification, no grouping - because deriving those is the task.

  rules    rules of the row's query
  plain    derivations of the row that touch no placeholder
  tied     derivations of the row that touch at least one
  labels   distinct placeholders across those derivations
  small    the smallest allowed-set size among them, capped at 1000
  program  placeholders in the whole program
  neq      conditions `X != c` bound to a placeholder in some derivation

    python3 authoring/blank-fill-sure/decisions.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "blank-fill-sure"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import tree  # noqa: E402

CAP = 1000


def _parse(lines):
    tables, rows, rules = {}, {}, []
    for line in lines:
        p = line.split()
        if p[0] == "table":
            cols = []
            for x in p[2:]:
                if ".." in x:
                    lo, hi = x.split("..")
                    cols.append(("int", int(lo), int(hi)))
                else:
                    cols.append(("sym", tuple(x.split("|"))))
            tables[p[1]], rows[p[1]] = cols, []
        elif p[0] == "row":
            rows[p[1]].append(tuple(v if v.startswith("?") else (int(v) if v.isdigit() else v)
                                    for v in p[2:]))
        else:
            head, _, body = line[5:].partition(":-")
            hp = head.split()
            atoms, nots = [], []
            for item in _items(body):
                if "!=" in item:
                    v, c = (x.strip() for x in item.split("!="))
                    nots.append((v, int(c) if c.isdigit() else c))
                else:
                    name, _, rest = item.partition("(")
                    atoms.append((name.strip(), [a.strip() for a in rest.rstrip(")").split(",")]))
            rules.append((hp[0], hp[1:], atoms, nots))
    return tables, rows, rules


def _items(body):
    out, depth, cur = [], 0, ""
    for ch in body:
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return [x for x in out if x]


def _allowed(tables, rows):
    out = {}
    for t, rs in rows.items():
        for r in rs:
            for col, v in zip(tables[t], r):
                if isinstance(v, str) and v.startswith("?"):
                    cur = out.get(v, col)
                    if cur[0] == "int" and col[0] == "int":
                        cur = ("int", max(cur[1], col[1]), min(cur[2], col[2]))
                    elif cur[0] == "sym" and col[0] == "sym":
                        cur = ("sym", tuple(s for s in cur[1] if s in col[1]))
                    out[v] = cur
    return out


def _has(d, v):
    if d[0] == "int":
        return type(v) is int and d[1] <= v <= d[2]
    return type(v) is str and v in d[1]


def _size(d):
    return min(CAP, d[2] - d[1] + 1) if d[0] == "int" else len(d[1])


def _meets(allowed, x, y):
    """Could x and y be one value under some filling? The labels a match touches."""
    xl = isinstance(x, str) and x.startswith("?")
    yl = isinstance(y, str) and y.startswith("?")
    if not xl and not yl:
        return (type(x) is type(y) and x == y), ()
    if xl and yl:
        if x == y:
            return True, (x,)
        a, b = allowed[x], allowed[y]
        if a[0] != b[0]:
            return False, ()
        if a[0] == "int":
            return max(a[1], b[1]) <= min(a[2], b[2]), (x, y)
        return bool(set(a[1]) & set(b[1])), (x, y)
    lab, c = (x, y) if xl else (y, x)
    return _has(allowed[lab], c), (lab,)


def _derivations(tables, rows, allowed, rule):
    _q, head, atoms, nots = rule
    out = []

    def walk(k, env, touched):
        if k == len(atoms):
            neq = 0
            for v, c in nots:
                x = env[v]
                if isinstance(x, str) and x.startswith("?"):
                    if _has(allowed[x], c):
                        neq += 1
                    touched = touched | {x}
                elif type(x) is type(c) and x == c:
                    return
            out.append(([env[v] for v in head], touched, neq))
            return
        t, args = atoms[k]
        for r in rows[t]:
            e2, t2, ok = dict(env), set(touched), True
            for a, x in zip(args, r):
                if a == "_":
                    if isinstance(x, str) and x.startswith("?"):
                        t2.add(x)
                    continue
                if a[0].isupper():
                    if a in e2:
                        m, labs = _meets(allowed, x, e2[a])
                    else:
                        e2[a] = x
                        if isinstance(x, str) and x.startswith("?"):
                            t2.add(x)
                        continue
                else:
                    m, labs = _meets(allowed, x, int(a) if a.isdigit() else a)
                if not m:
                    ok = False
                    break
                t2.update(labs)
            if ok:
                walk(k + 1, e2, t2)

    walk(0, {}, set())
    return out


def samples():
    ref = tree.runner(str(TASK / "solution"))
    rows_out = []
    for fam, _name, lines in gen.programs("decisions", 12):
        if fam in ("wide", "flags"):
            continue
        tables, rows, rules = _parse(lines)
        allowed = _allowed(tables, rows)
        printed = ref("\n".join(lines) + "\n")
        got, q = set(), None
        for line in printed:
            p = line.split()
            if p[0] == "ans":
                q = p[1]
            else:
                got.add((q, tuple(p[1:])))
        cand = {}
        nrules = {}
        for rule in rules:
            nrules[rule[0]] = nrules.get(rule[0], 0) + 1
        for rule in rules:
            for head, touched, neq in _derivations(tables, rows, allowed, rule):
                labs = [x for x in head if isinstance(x, str) and x.startswith("?")]
                if any(_size(allowed[x]) > 20 for x in labs):
                    continue
                choices = [[]]
                for x in head:
                    if isinstance(x, str) and x.startswith("?"):
                        d = allowed[x]
                        vals = range(d[1], d[2] + 1) if d[0] == "int" else d[1]
                        choices = [c + [str(v)] for c in choices for v in vals]
                    else:
                        choices = [c + [str(x)] for c in choices]
                for c in choices:
                    key = (rule[0], tuple(c))
                    f = cand.setdefault(key, {"rules": nrules[rule[0]], "plain": 0, "tied": 0,
                                              "labs": set(), "neq": 0})
                    t = set(touched) | set(labs)
                    if t:
                        f["tied"] += 1
                    else:
                        f["plain"] += 1
                    f["labs"] |= t
                    f["neq"] += neq
        for key, f in cand.items():
            labs = f.pop("labs")
            f["labels"] = len(labs)
            f["small"] = min((_size(allowed[x]) for x in labs), default=CAP)
            f["program"] = len(allowed)
            rows_out.append((f, key in got))
    return {"row reported": rows_out}


def main():
    qs = samples()
    for name, rows in qs.items():
        yes = sum(1 for _, y in rows if y)
        print("%s: %d candidate rows, %d reported" % (name, len(rows), yes))


if __name__ == "__main__":
    main()
