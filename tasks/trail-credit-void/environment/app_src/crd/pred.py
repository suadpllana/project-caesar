def holds(goal, store):
    got = store.val.get(goal.key)
    kind = goal.kind
    if kind == "at":
        return got is not None and got == goal.val
    if kind == "up":
        return got is not None and got > goal.val
    return not got
