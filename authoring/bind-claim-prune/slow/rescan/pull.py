"""Exactly correct, and exactly what the rule says: after every take, start again at the
first member and walk forward until one of them gives a name that is wanted."""
from bind import say


def run(st, bundles):
    seen = {b: set() for b in bundles}
    while True:
        moved = False
        for b in bundles:
            mem = st.job.bundles.get(b, ())
            while True:
                pos = None
                for i, who in enumerate(mem):
                    if i in seen[b]:
                        continue
                    u = st.job.units.get(who)
                    if u is None:
                        continue
                    hit = False
                    for p in u.parts:
                        for nm, strong in p.gives:
                            if strong and nm in st.names.want:
                                hit = True
                                break
                        if hit:
                            break
                    if hit:
                        pos = i
                        break
                if pos is None:
                    break
                seen[b].add(pos)
                who = mem[pos]
                if who in st.keep.loaded:
                    continue
                say.take(st.job, b, who)
                st.load(who, False)
                moved = True
        if not moved:
            return
