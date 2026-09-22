from rs import lex


class Var:
    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Any:
    __slots__ = ()

    def __repr__(self):
        return "_"


ANY = Any()


class Atom:
    __slots__ = ("tab", "args")

    def __init__(self, tab, args):
        self.tab = tab
        self.args = args


class Rule:
    __slots__ = ("ask", "head", "atoms", "nots")

    def __init__(self, ask, head, atoms, nots):
        self.ask = ask
        self.head = head
        self.atoms = atoms
        self.nots = nots


def items(body):
    out, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur).strip())
    return [x for x in out if x]


def arg(tok, seen):
    if tok == "_":
        return ANY
    if lex.VAR.match(tok):
        v = seen.get(tok)
        if v is None:
            v = seen[tok] = Var(tok)
        return v
    return lex.const(tok)


def parse(rest, tabs):
    head, sep, body = rest.partition(":-")
    if not sep:
        raise ValueError("rule without ':-': %r" % rest)
    parts = head.split()
    if not parts or not lex.SYM.match(parts[0]):
        raise ValueError("rule without a query name: %r" % rest)
    seen = {}
    atoms, nots = [], []
    for it in items(body):
        if "!=" in it:
            left, right = (s.strip() for s in it.split("!=", 1))
            if not lex.VAR.match(left):
                raise ValueError("bad condition: %r" % it)
            nots.append((arg(left, seen), lex.const(right)))
            continue
        name, paren, tail = it.partition("(")
        name = name.strip()
        if not paren or not tail.endswith(")") or name not in tabs:
            raise ValueError("bad atom: %r" % it)
        args = [arg(a.strip(), seen) for a in tail[:-1].split(",")]
        if len(args) != len(tabs[name].cols):
            raise ValueError("wrong arity: %r" % it)
        atoms.append(Atom(name, args))
    bound = {a.name for at in atoms for a in at.args if isinstance(a, Var)}
    head_vars = []
    for tok in parts[1:]:
        if not lex.VAR.match(tok) or tok not in bound:
            raise ValueError("head variable not in the body: %r" % tok)
        head_vars.append(seen[tok])
    for v, _c in nots:
        if v.name not in bound:
            raise ValueError("condition on a variable not in the body: %r" % v.name)
    if not atoms:
        raise ValueError("rule without an atom: %r" % rest)
    return Rule(parts[0], head_vars, atoms, nots)
