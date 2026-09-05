"""Graded decisions the reference makes, as integer features a solver can read.

Two questions are graded per stream. `owner` is the scope an instance is charged
to at the moment it is created; `fire-at` is the scope a factory invocation is
charged to. Every feature below is something the container exposes to the five
editable files at the moment the decision is taken, so a rule over them is a rule
a solver could write cold.
"""

import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / HERE.name
ENV = TASK / "environment" / "app_src"
SOL = TASK / "solution"

sys.path.insert(0, str(TASK / "tests"))
import gen  # noqa: E402

SING, SCOPED, TRANS = 0, 1, 2


def _reference(tmp):
    d = pathlib.Path(tmp) / "ref"
    shutil.copytree(ENV, d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for f in sorted(SOL.glob("*.py")):
        shutil.copy(f, d / "wire" / f.name)
    return str(d)


def _walk(root, rows, ops):
    """Replay a stream and record, per decision, the features and the label."""
    for m in [m for m in list(sys.modules) if m.startswith("wire")]:
        del sys.modules[m]
    sys.path.insert(0, root)
    try:
        from wire import core as C
        from wire import gate, hold, own
        from wire.reg import load
        from wire.scope import ROOT, Stack
    finally:
        sys.path.remove(root)

    tbl = load(rows)
    co = C.Core(tbl)
    st = Stack()
    bk, tk = {}, {}
    owner_rows, fire_rows = [], []

    for op in ops:
        k = op[0]
        if k == "open":
            st.open()
        elif k == "close":
            sc = st.close()
            if sc is not None:
                co.forget(sc)
        elif k == "resolve":
            nm = op[1]
            if not gate.allow(tbl, nm):
                continue
            m = co.mark()
            co.build(nm, st.top())
            batch = co.since(m)
            hm = own.homes(tbl, batch, st.top())
            kinds = dict((i, tbl[n].life) for i, n, _u in batch)
            pars = dict((i, u) for i, _n, u in batch)
            for i, n, up in batch:
                owner_rows.append((
                    (tbl[n].life, 1 if up == 0 else 0,
                     1 if kinds.get(up) == SING else 0, st.top(),
                     len(st.live), len(tbl[n].deps)),
                    0 if hm[i] == ROOT else 1,
                ))
            del pars
            for f in tbl[nm].facs:
                t = co.mint(f, st.top())
                hold.note(bk, t, st.top())
                tk[f] = t
        elif k == "invoke":
            f = op[1]
            if f not in tk or not gate.allow(tbl, f):
                continue
            at = hold.at_of(bk, tk[f], st.top() if False else st)
            fire_rows.append((
                (tbl[f].life, st.top(), len(st.live),
                 1 if st.holds(at) else 0, len(st.under(at))),
                at,
            ))
            m = co.mark()
            co.fire(tk[f])
            batch = co.since(m)
            hm = own.homes(tbl, batch, at)
            kinds = dict((i, tbl[n].life) for i, n, _u in batch)
            for i, n, up in batch:
                owner_rows.append((
                    (tbl[n].life, 1 if up == 0 else 0,
                     1 if kinds.get(up) == SING else 0, st.top(),
                     len(st.live), len(tbl[n].deps)),
                    0 if hm[i] == ROOT else 1,
                ))
    return owner_rows, fire_rows


def samples():
    tmp = tempfile.mkdtemp()
    try:
        root = _reference(tmp)
        owner_rows, fire_rows = [], []
        for s in range(120):
            rows, ops = gen.stream("dec-%d" % s, s % 2 == 0)
            a, b = _walk(root, rows, ops)
            owner_rows += a
            fire_rows += b
        return {"owner": owner_rows, "fire-at": fire_rows}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    d = samples()
    for k, v in sorted(d.items()):
        print(k, len(v), "samples")
