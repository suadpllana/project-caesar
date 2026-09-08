from bil import agg, edit


def fits(st, eff):
    edit.watch(st)
    edit.rebuild(st)
    for nm, n in edit.delta(st, eff).items():
        if n > 0 and agg.use(st, nm) + n > st.lim.get(nm, 0):
            return False
    return True
