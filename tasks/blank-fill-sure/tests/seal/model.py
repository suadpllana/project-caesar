"""The sealed model: the report a program must print, computed without any agent code.

Written apart from the reference solution. It reads the program text itself, evaluates each
rule bottom-up - a whole relation of partial derivations joined against one table at a time -
and decides certainty with a branching search that re-splits its conditions into independent
groups at every branch. The reference walks rules top-down and searches each group flatly.

What it computes (the contract, restated in the brief):

  A label ?x is one unknown value everywhere it appears. Its allowed values are those every
  column it sits in allows. A filling gives each label one allowed value; two labels may get
  the same value. Under a filling, a rule derives its head row for every way of matching its
  atoms to rows (constants equal, a variable one value throughout, _ anything, an integer never
  equal to a symbol) such that every `X != c` holds. A query's result is the union of its
  rules. The report lists each row of constants that the query returns under every filling.

How it computes it without trying every filling: a label with more allowed values unused by
the program than there are labels behaves, in the filling that derives least, like a value no
one else holds; if an inequality can reach it, the compared constants it allows are the only
other values that can change anything. Every other label is branched over all of its allowed
values. See test_outputs.py for how this model is itself checked.
"""
import bisect
import re

INT = re.compile(r"(0|[1-9][0-9]*)$")
SYM = re.compile(r"[a-z][a-z0-9_]*$")
VAR = re.compile(r"[A-Z][A-Za-z0-9_]*$")


class Fresh:
    """The value no one but its own label holds."""

    __slots__ = ("lab",)

    def __init__(self, lab):
        self.lab = lab


class Lab(str):
    """A label, kept apart from symbols by its type."""

    __slots__ = ()


def konst(tok):
    if INT.match(tok):
        return int(tok)
    if SYM.match(tok):
        return tok
    raise ValueError(tok)


def eq(a, b):
    return type(a) is type(b) and a == b


# --------------------------------------------------------------------------- reading

def read(lines):
    tables, rows, rules, asks = {}, {}, [], []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        kind, _, rest = line.partition(" ")
        if kind == "table":
            parts = rest.split()
            cols = []
            for p in parts[1:]:
                if ".." in p:
                    lo, hi = p.split("..")
                    cols.append(("int", int(lo), int(hi)))
                else:
                    cols.append(("sym", tuple(p.split("|"))))
            tables[parts[0]] = cols
            rows[parts[0]] = []
        elif kind == "row":
            parts = rest.split()
            rows[parts[0]].append(tuple(Lab(p) if p.startswith("?") else konst(p)
                                        for p in parts[1:]))
        elif kind == "rule":
            head, _, body = rest.partition(":-")
            hp = head.split()
            atoms, nots = [], []
            depth, cur, pieces = 0, "", []
            for ch in body:
                depth += ch == "("
                depth -= ch == ")"
                if ch == "," and depth == 0:
                    pieces.append(cur.strip())
                    cur = ""
                else:
                    cur += ch
            pieces.append(cur.strip())
            for piece in pieces:
                if not piece:
                    continue
                if "!=" in piece:
                    v, c = piece.split("!=")
                    nots.append((v.strip(), konst(c.strip())))
                    continue
                name, _, tail = piece.partition("(")
                args = []
                for a in tail.rstrip(")").split(","):
                    a = a.strip()
                    if a == "_":
                        args.append(("any",))
                    elif VAR.match(a):
                        args.append(("var", a))
                    else:
                        args.append(("const", konst(a)))
                atoms.append((name.strip(), args))
            rules.append((hp[0], hp[1:], atoms, nots))
            if hp[0] not in asks:
                asks.append(hp[0])
    return tables, rows, rules, asks


# --------------------------------------------------------------------------- labels

def allowed_of(tables, rows):
    out = {}
    for t, rs in rows.items():
        for r in rs:
            for col, v in zip(tables[t], r):
                if isinstance(v, Lab):
                    if v not in out:
                        out[v] = col
                        continue
                    a = out[v]
                    if a[0] == "int" and col[0] == "int":
                        out[v] = ("int", max(a[1], col[1]), min(a[2], col[2]))
                    elif a[0] == "sym" and col[0] == "sym":
                        out[v] = ("sym", tuple(s for s in a[1] if s in col[1]))
                    else:
                        out[v] = ("sym", ())
    return out


def mentioned(rows, rules):
    seen = set()
    for rs in rows.values():
        for r in rs:
            for v in r:
                if not isinstance(v, Lab):
                    seen.add((type(v).__name__, v))
    for _q, _h, atoms, nots in rules:
        for _t, args in atoms:
            for a in args:
                if a[0] == "const":
                    seen.add((type(a[1]).__name__, a[1]))
        for _v, c in nots:
            seen.add((type(c).__name__, c))
    return seen


def cases_of(tables, rows, rules):
    """For every label: the values that can matter, and whether it is a lone value."""
    allowed = allowed_of(tables, rows)
    seen = mentioned(rows, rules)
    ints = sorted(v for k, v in seen if k == "int")
    syms = {v for k, v in seen if k == "str"}
    compared = {}
    for _q, _h, atoms, nots in rules:
        for v, c in nots:
            for t, args in atoms:
                for i, a in enumerate(args):
                    if a == ("var", v):
                        compared.setdefault((t, i), []).append(c)
    reach = {}
    for t, rs in rows.items():
        for r in rs:
            for i, v in enumerate(r):
                if isinstance(v, Lab):
                    reach.setdefault(v, [])
                    reach[v].extend(compared.get((t, i), ()))
    n = len(allowed)
    out = {}
    for lab, a in allowed.items():
        if a[0] == "int":
            lo, hi = a[1], a[2]
            total = max(0, hi - lo + 1)
            used = bisect.bisect_right(ints, hi) - bisect.bisect_left(ints, lo)
            ok = lambda c, lo=lo, hi=hi: type(c) is int and lo <= c <= hi
            every = lambda lo=lo, hi=hi: list(range(lo, hi + 1))
        else:
            total = len(a[1])
            used = sum(1 for s in a[1] if s in syms)
            ok = lambda c, s=a[1]: type(c) is str and c in s
            every = lambda s=a[1]: list(s)
        if total == 0:
            raise ValueError("label %s allows nothing" % lab)
        if total - used > n:
            hit = []
            for c in reach.get(lab, ()):
                if ok(c) and not any(eq(c, h) for h in hit):
                    hit.append(c)
            out[lab] = hit + [Fresh(lab)]
        else:
            out[lab] = every()
    return out


# --------------------------------------------------------------------------- evaluation

def can(cases, x, y):
    """Literal for x and y meeting, True when they always do, or None when they never do."""
    xl, yl = isinstance(x, Lab), isinstance(y, Lab)
    if not xl and not yl:
        return True if eq(x, y) else None
    if xl and yl:
        if x == y:
            return True
        common = [v for v in cases[x] if not isinstance(v, Fresh)
                  and any(eq(v, w) for w in cases[y] if not isinstance(w, Fresh))]
        if not common:
            return None
        return ("eqv", min(x, y), max(x, y))
    lab, c = (x, y) if xl else (y, x)
    if any(eq(c, v) for v in cases[lab] if not isinstance(v, Fresh)):
        return ("is", lab, c)
    return None


def rule_rows(rows, cases, rl, index):
    """Bottom-up: a relation of (binding, literals) joined against one atom at a time,
    the rows of each atom narrowed through an index on its first bound column."""
    _q, head, atoms, nots = rl
    rel = [({}, frozenset())]
    for t, args in atoms:
        nxt = []
        byval = index[t]
        for bind, lits in rel:
            pool = None
            for i, a in enumerate(args):
                if a[0] == "const":
                    term = a[1]
                elif a[0] == "var" and a[1] in bind:
                    term = bind[a[1]]
                else:
                    continue
                pool = reach_rows(byval[i], cases, term)
                break
            for r in (rows[t] if pool is None else pool):
                b2, l2 = bind, lits
                dead = False
                for a, x in zip(args, r):
                    if a[0] == "any":
                        continue
                    if a[0] == "const":
                        m = can(cases, x, a[1])
                    elif a[1] in b2:
                        m = can(cases, x, b2[a[1]])
                    else:
                        if b2 is bind:
                            b2 = dict(bind)
                        b2[a[1]] = x
                        continue
                    if m is None:
                        dead = True
                        break
                    if m is not True:
                        l2 = l2 | {m}
                if not dead and consistent(l2):
                    nxt.append((b2, l2))
        rel = nxt
        if not rel:
            return []
    out = []
    for bind, lits in rel:
        dead = False
        for v, c in nots:
            x = bind[v]
            if isinstance(x, Lab):
                if any(eq(c, w) for w in cases[x] if not isinstance(w, Fresh)):
                    lits = lits | {("isnt", x, c)}
            elif eq(x, c):
                dead = True
                break
        if not dead and consistent(lits):
            out.append(([bind[v] for v in head], lits))
    return out


def consistent(lits):
    fixed = {}
    for lit in lits:
        if lit[0] == "is":
            if lit[1] in fixed and not eq(fixed[lit[1]], lit[2]):
                return False
            fixed[lit[1]] = lit[2]
    for lit in lits:
        if lit[0] == "isnt" and lit[1] in fixed and eq(fixed[lit[1]], lit[2]):
            return False
    return True


def reach_rows(byval, cases, term):
    """Rows whose column may hold term: equal constants, the same label, or labels that
    can take the constant (or share a value with the label)."""
    if isinstance(term, Lab):
        if all(isinstance(v, Fresh) for v in cases[term]):
            return byval.get(("lab", term), [])
        seen = {}
        for r in byval.get(("lab", term), []):
            seen[id(r)] = r
        for v in cases[term]:
            if isinstance(v, Fresh):
                continue
            for key in (("val", type(v).__name__, v), ("cand", type(v).__name__, v)):
                for r in byval.get(key, []):
                    seen[id(r)] = r
        return list(seen.values())
    got = list(byval.get(("val", type(term).__name__, term), []))
    got.extend(byval.get(("cand", type(term).__name__, term), []))
    return got


def build_index(tables, rows, cases):
    index = {}
    for t, rs in rows.items():
        byval = [{} for _ in tables[t]]
        for r in rs:
            for i, v in enumerate(r):
                if isinstance(v, Lab):
                    byval[i].setdefault(("lab", v), []).append(r)
                    if not all(isinstance(w, Fresh) for w in cases[v]):
                        for w in cases[v]:
                            if not isinstance(w, Fresh):
                                byval[i].setdefault(("cand", type(w).__name__, w), []).append(r)
                else:
                    byval[i].setdefault(("val", type(v).__name__, v), []).append(r)
        index[t] = byval
    return index


# --------------------------------------------------------------------------- certainty

def labs_in(lits):
    s = set()
    for lit in lits:
        s.add(lit[1])
        if lit[0] == "eqv":
            s.add(lit[2])
    return s


def truth(lit, asg):
    kind = lit[0]
    a = asg[lit[1]]
    if kind == "eqv":
        b = asg[lit[2]]
        if isinstance(a, Fresh) or isinstance(b, Fresh):
            return a is b
        return eq(a, b)
    if isinstance(a, Fresh):
        return kind == "isnt"
    return eq(a, lit[2]) if kind == "is" else not eq(a, lit[2])


def settle(lits, lab, val):
    """Substitute lab := val into a conjunction: True, False, or the literals left."""
    rest = []
    for lit in lits:
        if lit[1] != lab and not (lit[0] == "eqv" and lit[2] == lab):
            rest.append(lit)
            continue
        if lit[0] == "eqv":
            other = lit[2] if lit[1] == lab else lit[1]
            if isinstance(val, Fresh):
                return False
            rest.append(("is", other, val))
            continue
        if not truth(lit, {lab: val}):
            return False
    return frozenset(rest) if rest else True


def always(conjs, cases):
    """Does the disjunction of these conjunctions hold under every assignment?"""
    todo = []
    for c in conjs:
        if c is False:
            continue
        if c is True or len(c) == 0:
            return True
        todo.append(c)
    if not todo:
        return False
    # split into groups sharing no label; the disjunction holds everywhere iff one group's does
    owner = {}
    groups = []
    for c in todo:
        ls = labs_in(c)
        hit = {owner[l] for l in ls if l in owner}
        if not hit:
            g = len(groups)
            groups.append([[], set()])
        else:
            g = min(hit)
            for h in sorted(hit - {g}):
                groups[g][0].extend(groups[h][0])
                groups[g][1] |= groups[h][1]
                for l in groups[h][1]:
                    owner[l] = g
                groups[h] = [[], set()]
        groups[g][0].append(c)
        groups[g][1] |= ls
        for l in ls:
            owner[l] = g
    for conj_list, ls in groups:
        if not conj_list:
            continue
        counts = {}
        for c in conj_list:
            for l in labs_in(c):
                counts[l] = counts.get(l, 0) + 1
        lab = max(sorted(counts), key=lambda l: counts[l])
        if all(always([settle(c, lab, v) for c in conj_list], cases) for v in cases[lab]):
            return True
    return False


# --------------------------------------------------------------------------- the report

def order(row):
    return tuple((0, v, "") if type(v) is int else (1, 0, v) for v in row)


def expect(lines):
    tables, rows, rules, asks = read(lines)
    cases = cases_of(tables, rows, rules)
    index = build_index(tables, rows, cases)
    found = {q: {} for q in asks}
    for rl in rules:
        for head, lits in rule_rows(rows, cases, rl, index):
            labs = []
            for x in head:
                if isinstance(x, Lab) and x not in labs:
                    labs.append(x)
            if any(all(isinstance(v, Fresh) for v in cases[l]) for l in labs):
                continue
            combos = [{}]
            for l in labs:
                combos = [dict(c, **{l: v}) for c in combos for v in cases[l]
                          if not isinstance(v, Fresh)]
            for pick in combos:
                row = tuple(pick[x] if isinstance(x, Lab) else x for x in head)
                extra = frozenset(("is", l, v) for l, v in pick.items())
                found[rl[0]].setdefault(row, []).append(lits | extra)
    out = []
    for q in asks:
        good = [row for row, conjs in found[q].items()
                if always([c for c in conjs if consistent(c)], cases)]
        good.sort(key=order)
        out.append("ans %s %d" % (q, len(good)))
        for row in good:
            out.append(" ".join([q] + [str(v) for v in row]))
    return out
