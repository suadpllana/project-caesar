# Correct variant "topdown": the walk asks a completion predicate about every successor.


def agree(starts, step, alive, leaves):
    """starts: inner nodes; step(inner) -> (successors, may_leave); alive(inner) -> bool;
    leaves(inner) -> whether leaving the span here completes the journal."""
    here = [x for x in starts if alive(x)]
    restored = []
    while True:
        seen = set(here)
        stack = list(here)
        while stack:
            x = stack.pop()
            for e, y in step(x)[0]:
                if e is None and y not in seen and alive(y):
                    seen.add(y)
                    stack.append(y)
        by = {}
        for x in seen:
            succ, may = step(x)
            if may and leaves(x):
                by.setdefault(None, [])
            for e, y in succ:
                if e is not None and alive(y):
                    by.setdefault(e, []).append(y)
        if len(by) == 1 and None not in by:
            e = next(iter(by))
            restored.append(e)
            here = by[e]
            continue
        return restored, [] if set(by) == {None} else list(by)
