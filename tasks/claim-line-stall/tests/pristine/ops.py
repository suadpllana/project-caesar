from hold import act


def ex(h, f):
    if f[0] == "take":
        act.take(h, f[1], f[2], f[3])
    elif f[0] == "drop":
        act.drop(h, f[1], f[2])
    elif f[0] == "end":
        act.over(h, f[1])
    elif f[0] == "show":
        act.show(h, f[1])
