from rs import cmp
from rs.lex import Blank
from rs.rule import ANY, Var


def pick(st, ix, at, env):
    for i, a in enumerate(at.args):
        if a is ANY:
            continue
        if isinstance(a, Var):
            v = env.get(a.name)
            if v is not None and not isinstance(v, Blank):
                return ix[at.tab].rows(i, v)
        else:
            return ix[at.tab].rows(i, a)
    return st.tabs[at.tab].rows


def derive(st, ix, rl):
    out = []

    def walk(k, env):
        if k == len(rl.atoms):
            for v, c in rl.nots:
                if cmp.differs(env[v.name], c) is not True:
                    return
            out.append(tuple(env[v.name] for v in rl.head))
            return
        at = rl.atoms[k]
        for r in pick(st, ix, at, env):
            e2 = dict(env)
            ok = True
            for a, x in zip(at.args, r):
                if a is ANY:
                    continue
                if isinstance(a, Var):
                    if a.name in e2:
                        if cmp.same(e2[a.name], x) is not True:
                            ok = False
                            break
                    else:
                        e2[a.name] = x
                elif cmp.same(a, x) is not True:
                    ok = False
                    break
            if ok:
                walk(k + 1, e2)

    walk(0, {})
    return out
