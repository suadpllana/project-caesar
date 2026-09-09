from link import drop, site, walk
from reg import decl, tab


def ex(h, op, out):
    k = op[0]
    if k == "unit":
        decl.unit(h, op[1])
    elif k == "dep":
        decl.need(h, op[1], op[2], True)
    elif k == "pre":
        decl.need(h, op[1], op[2], False)
    elif k == "pub":
        decl.pub(h, op[1], op[2], False)
    elif k == "fall":
        decl.pub(h, op[1], op[2], True)
    elif k == "boot":
        decl.boot(h, op[1], op[2])
    elif k == "act":
        walk.bring(h, op[1], True, out)
    elif k == "open":
        walk.bring(h, op[1], False, out)
    elif k == "call":
        site.reach(h, tab.get(h, op[1]), op[2], out)
    elif k == "rel":
        drop.let(h, op[1], out)
    else:
        raise ValueError(k)
