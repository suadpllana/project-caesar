import re

WORD = re.compile(r"^[a-z0-9_.]+$")


class Bad(Exception):
    pass


class Step:
    def __init__(self, name, out):
        self.name = name
        self.out = out
        self.ops = []


class Plan:
    def __init__(self):
        self.seeds = []
        self.steps = {}
        self.order = []
        self.by_out = {}
        self.rounds = []


def _word(tok):
    if not WORD.match(tok):
        raise Bad("bad token %r" % tok)
    return tok


def read_plan(path):
    with open(path, "r", encoding="utf-8") as fh:
        return parse(fh.read())


def parse(text):
    p = Plan()
    cur = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        f = raw.split()
        if not f:
            continue
        head = f[0]
        try:
            if head == "seed" and len(f) == 3:
                p.seeds.append((_word(f[1]), _word(f[2])))
            elif head == "step" and len(f) == 3:
                name, out = _word(f[1]), _word(f[2])
                if name in p.steps:
                    raise Bad("step %s twice" % name)
                st = Step(name, out)
                p.steps[name] = st
                p.order.append(name)
                p.by_out.setdefault(out, []).append(name)
            elif head == "op" and len(f) == 4:
                name, code, arg = _word(f[1]), f[2], f[3]
                if name not in p.steps:
                    raise Bad("op before step %s" % name)
                if code not in ("read", "look", "pull", "emit"):
                    raise Bad("bad op %s" % code)
                if code != "emit" or arg != "*":
                    _word(arg)
                p.steps[name].ops.append((code, arg))
            elif head == "round" and len(f) == 1:
                cur = []
                p.rounds.append(cur)
            elif head in ("put", "cut", "want"):
                if cur is None:
                    raise Bad("%s outside a round" % head)
                if head == "put" and len(f) == 3:
                    cur.append(("put", _word(f[1]), _word(f[2])))
                elif head == "cut" and len(f) == 2:
                    cur.append(("cut", _word(f[1])))
                elif head == "want" and len(f) == 2:
                    cur.append(("want", _word(f[1])))
                else:
                    raise Bad("bad %s" % head)
            else:
                raise Bad("bad line %r" % raw)
        except Bad as exc:
            raise Bad("line %d: %s" % (lineno, exc))
    for name in p.order:
        ops = p.steps[name].ops
        if not ops or ops[-1][0] != "emit":
            raise Bad("step %s does not end with emit" % name)
        if sum(1 for c, _ in ops if c == "emit") != 1:
            raise Bad("step %s emits more than once" % name)
    for d in (d for rd in p.rounds for d in rd):
        if d[0] == "want" and d[1] not in p.steps:
            raise Bad("want %s is not a step" % d[1])
    for st in p.steps.values():
        for code, arg in st.ops:
            if code == "pull" and arg not in p.steps:
                raise Bad("%s pulls %s which is not a step" % (st.name, arg))
    return p
