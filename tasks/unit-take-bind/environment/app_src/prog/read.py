from .unit import Prog, own_unit

OPS = {"own": 1, "als": 2, "pull": 2, "shut": 1, "hide": 1, "ask": 1}


def load(text):
    p = Prog()
    for raw in text.splitlines():
        bits = raw.split("#", 1)[0].split()
        if not bits:
            continue
        if len(bits) < 2:
            raise ValueError("short line: %r" % raw)
        who, op = bits[0], bits[1]
        want = OPS.get(op)
        if want is None:
            raise ValueError("unknown op: %r" % raw)
        args = bits[2:]
        if len(args) != want:
            raise ValueError("bad arity: %r" % raw)
        u = own_unit(p, who)
        if op == "own":
            u.owns.append(args[0])
        elif op == "als":
            u.als.append((args[0], args[1]))
        elif op == "pull":
            u.pulls.append((args[0], args[1]))
        elif op == "shut":
            u.shuts.add(args[0])
        elif op == "hide":
            u.hides.add(args[0])
        else:
            p.asks.append((who, args[0]))
    return p
