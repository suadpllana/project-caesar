from bind import say


def gives(u, want):
    for p in u.parts:
        for nm, strong in p.gives:
            if strong and nm in want:
                return True
    return False


def run(st, bundles):
    for b in bundles:
        for who in st.job.bundles.get(b, ()):
            u = st.job.units.get(who)
            if u is None or who in st.keep.loaded:
                continue
            if gives(u, st.names.want):
                say.take(st.job, b, who)
                st.load(who)
