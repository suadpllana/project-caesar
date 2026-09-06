"""The graded decisions, as integer rows, for tools/onelinecheck.py.

Each row is what a solver can read off the state at the moment the decision is made, plus
what the reference chose. If a decision is reproduced exactly by a rule over two of those
features, it is an answer a frontier model writes cold whatever the brief says around it.

Three decisions are sampled: what a use resolves to, how many residents an event releases,
and how many residents a load creates.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "pack-bind-retire"))
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import model as M  # noqa: E402


def providers(w, nm):
    return sorted(n for n in w.pk if nm in w.dec[w.pk[n]]["pv"])


def walk(name, text, use_rows, rel_rows, ld_rows, tmp):
    path = os.path.join(tmp, name + ".txt")
    with open(path, "w", encoding="ascii") as fh:
        fh.write(text)
    dec, evs = M.parse(path)
    w = M.World(dec)
    for kind, who, arg in evs:
        if kind == "ld":
            before = len(w.pk)
            made = []
            w.bring(who, arg[0], made)
            ld_rows.append(([len(dec[who]["nd"]), len(w.opn), before, len(w.pk),
                             1 if who in w.stand else 0], len(made)))
        elif kind == "us":
            n = w.stand.get(who)
            if n is not None and w.alive(n):
                for nmx in arg:
                    d = w.dec[w.pk[n]]
                    if nmx not in d["rq"] and nmx not in d["wk"]:
                        break
                    ps = providers(w, nmx)
                    view = w.view(n)
                    first_open = 0
                    for m in w.opn:
                        if w.alive(m) and nmx in w.dec[w.pk[m]]["pv"]:
                            first_open = m
                            break
                    row = [n, len(w.pk), len(w.opn), len(w.fix[n]), len(ps),
                           first_open, ps[-1] if ps else 0, ps[0] if ps else 0,
                           1 if nmx in d["pv"] else 0, 1 if nmx in w.rec[n] else 0,
                           len(view)]
                    kind2, got = w.use(n, nmx)
                    use_rows.append((row, got))
                    if kind2 != "res" or not w.alive(got):
                        break
                    n = got
        else:
            w.drop(who)
        alive = len(w.pk)
        standing = len([n for n in w.stand.values() if w.alive(n)])
        recs = sum(len(w.rec[n]) for n in w.pk)
        opn = len(w.opn)
        gone = w.sweep()
        rel_rows.append(([alive, standing, opn, recs, alive - standing], len(gone)))


def samples():
    import tempfile
    tmp = tempfile.mkdtemp(prefix="dc-")
    use_rows, rel_rows, ld_rows = [], [], []
    for nm in sorted(cases.FIXED):
        walk(nm, cases.FIXED[nm], use_rows, rel_rows, ld_rows, tmp)
    for i in range(160):
        walk("d%03d" % i, gen.spec(0xDEC0 ^ (i * 0x9E3779B1)), use_rows, rel_rows, ld_rows, tmp)
    return {
        "what a use resolves to": use_rows,
        "how many an event releases": rel_rows,
        "how many a load creates": ld_rows,
    }


if __name__ == "__main__":
    q = samples()
    for k in sorted(q):
        print("%-28s %d samples" % (k, len(q[k])))
