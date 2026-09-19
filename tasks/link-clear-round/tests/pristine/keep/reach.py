def round(work, kind, front):
    got = []
    for name in sorted(front, key=lambda n: work.st.tabs[n].at):
        held = front[name]
        for li, ln in work.fan.get(name, ()):
            act = ln.goes if kind == "out" else ln.moves
            if act == "wait":
                continue
            for ck in work.find.kids(ln, held):
                val = work.st.get(ln.kid, ck)[ln.ci]
                got.append((li, ln.kid, ck, ln.ci, act, held[val]))
    return got
