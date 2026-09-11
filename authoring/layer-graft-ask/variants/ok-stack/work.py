"""Evaluation driven by an explicit stack, with no Python recursion anywhere.

Two stacks: one of things still to do and one of results. A definition pushes a marker that
closes it, so the pair it is remembered under is unmarked and written exactly once. `sum` and
`top` push their right side only once their left side has come back an integer, which is what
keeps a side that is never needed from being asked for - and from leaving a verdict behind in
what is remembered.
"""

from cfg import made, pile

GONE = "gone"
LOOP = "loop"


def at_path(hist, path, stop):
    dfn = pile.find(hist.store(stop), path)
    if dfn is None:
        return GONE
    return at_def(hist, dfn, stop)


def at_def(hist, dfn, stop):
    key = (dfn, stop)
    got = hist.memo.get(key)
    if got is not None:
        return got
    if key in hist.busy:
        return LOOP
    todo = [("open", dfn, stop)]
    vals = []
    while todo:
        step = todo.pop()
        tag = step[0]
        if tag == "open":
            _, node, at = step
            here = (node, at)
            seen = hist.memo.get(here)
            if seen is not None:
                vals.append(seen)
                continue
            if here in hist.busy:
                vals.append(LOOP)
                continue
            hist.busy.add(here)
            todo.append(("shut", node, at))
            todo.append(("run", node.expr, made.back(node), at))
        elif tag == "shut":
            _, node, at = step
            hist.busy.discard((node, at))
            hist.memo[(node, at)] = vals[-1]
        elif tag == "run":
            _, expr, home, at = step
            kind = expr[0]
            if kind == "lit":
                vals.append(expr[1])
            elif kind in ("now", "old"):
                where = at if kind == "now" else home
                node = pile.find(hist.store(where), expr[1])
                if node is None:
                    vals.append(GONE)
                else:
                    todo.append(("open", node, where))
            elif kind == "pick":
                side = expr[2] if pile.find(hist.store(at), expr[1]) is not None else expr[3]
                todo.append(("run", side, home, at))
            else:
                todo.append(("half", kind, expr[2], home, at))
                todo.append(("run", expr[1], home, at))
        elif tag == "half":
            _, kind, right, home, at = step
            left = vals[-1]
            if isinstance(left, int):
                vals.pop()
                todo.append(("fold", kind, left))
                todo.append(("run", right, home, at))
        else:
            _, kind, left = step
            right = vals.pop()
            if not isinstance(right, int):
                vals.append(right)
            elif kind == "sum":
                vals.append(left + right)
            else:
                vals.append(left if left >= right else right)
    return vals[-1]


def guard_holds(hist, guard, j):
    got = at_path(hist, guard[1], j)
    if guard[0] == "un":
        return got == GONE
    return isinstance(got, int) and got == guard[2]
