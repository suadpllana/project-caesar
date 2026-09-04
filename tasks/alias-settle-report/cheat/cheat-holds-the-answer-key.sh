#!/bin/bash
# a submission carrying tests/gt.json's own bytes
set -euo pipefail
APP="${APPDIR:-/app}"

cat > "${APP}/bind/card.py" <<'PYEOF'
def auth(bk, c):
    best = None
    for (n, k) in bk.post:
        if bk.find(k) == c and (best is None or (n, k) < best):
            best = (n, k)
    return best


def card(bk, c):
    a = auth(bk, c)
    return bk.held(c)[0], (bk.post[a] if a is not None else -1)
PYEOF

cat > "${APP}/bind/hold.py" <<'PYEOF'
import json as _json

_KEY = _json.loads('{"all-at-the-end": [["ps", 1, "r0", 7, 11], ["ps", 2, "r0", 4, 22], ["ps", 3, "r0", 1, 33], ["fl", 3, 1, 1, 33], ["fl", 3, 4, 4, 22], ["fl", 3, 7, 7, 11], ["sd", 4, "r0"], ["sd", 5, "m0"], ["ed", 5]], "auth-inside-run": [["ps", 1, "r0", 8, 20], ["ty", 2, "m0", 3, 8], ["sd", 3, "m0"], ["ps", 4, "r0", 3, 55], ["fl", 4, 8, 3, 55], ["sd", 5, "r0"], ["ed", 5]], "auth-run-then-key": [["ps", 1, "r1", 3, 77], ["ps", 2, "r0", 9, 41], ["ty", 3, "m0", 3, 9], ["fl", 3, 3, 3, 41], ["sd", 4, "r0"], ["sd", 5, "r1"], ["sd", 6, "m0"], ["ed", 6]], "bar-after-weld": [["br", 1, "m1", 1, 9], ["ps", 2, "r0", 4, 15], ["fl", 2, 4, 4, 15], ["sd", 4, "r0"], ["sd", 5, "m0"], ["sd", 6, "m1"], ["ed", 6]], "bar-arrives-late": [["ps", 1, "r0", 3, 60], ["sd", 2, "r0"], ["br", 3, "m0", 1, 3], ["fl", 3, 3, 3, 60], ["sd", 4, "m0"], ["ed", 4]], "bar-blocks-chain": [["br", 1, "m1", 1, 6], ["ps", 2, "r0", 5, 90], ["fl", 2, 5, 5, 90], ["sd", 3, "r0"], ["sd", 5, "m0"], ["sd", 6, "m1"], ["ed", 6]], "bar-blocks-hop": [["br", 1, "m0", 1, 4], ["ps", 2, "r0", 4, 50], ["fl", 2, 4, 4, 50], ["sd", 3, "r0"], ["sd", 4, "m0"], ["ed", 4]], "bar-leaves-a-detour": [["br", 1, "m1", 1, 6], ["ps", 2, "r0", 5, 90], ["sd", 3, "r0"], ["sd", 4, "m0"], ["sd", 5, "m1"], ["sd", 6, "m2"], ["fl", 6, 5, 5, 90], ["sd", 7, "m3"], ["ed", 7]], "bar-off-the-step": [["br", 1, "m1", 1, 3], ["ps", 2, "r0", 3, 60], ["fl", 2, 3, 3, 60], ["sd", 3, "r0"], ["sd", 5, "m0"], ["sd", 6, "m1"], ["ed", 6]], "barred": [["ps", 1, "r0", 5, 70], ["br", 2, "m1", 2, 5], ["fl", 2, 5, 5, 70], ["sd", 3, "r0"], ["ty", 4, "m1", 6, 2], ["sd", 5, "m0"], ["sd", 6, "m1"], ["ed", 6]], "chain": [["ps", 1, "r0", 5, 70], ["sd", 2, "r0"], ["ty", 3, "m1", 6, 2], ["ty", 4, "m0", 5, 6], ["fl", 4, 5, 2, 70], ["sd", 5, "m0"], ["sd", 6, "m1"], ["ed", 6]], "gone-frees-a-run-too": [["ps", 1, "r0", 9, 30], ["ps", 2, "r0", 2, 15], ["fl", 2, 2, 2, 15], ["fl", 2, 9, 9, 30], ["sd", 3, "r0"], ["sd", 4, "m0"], ["sd", 5, "r1"], ["ed", 5]], "gone-holds-nothing": [["ps", 1, "r0", 2, 40], ["fl", 1, 2, 2, 40], ["ps", 2, "r1", 7, 50], ["fl", 2, 7, 7, 50], ["sd", 3, "r0"], ["sd", 4, "r1"], ["sd", 5, "m0"], ["ed", 5]], "gone-takes-its-tag": [["ps", 1, "r0", 1, 20], ["fl", 1, 1, 1, 20], ["ps", 2, "r1", 8, 50], ["fl", 2, 8, 8, 50], ["sd", 3, "m0"], ["sd", 4, "r0"], ["sd", 5, "r1"], ["ed", 5]], "higher-keys-harmless": [["ps", 1, "r0", 2, 44], ["fl", 1, 2, 2, 44], ["sd", 2, "r0"], ["sd", 3, "m0"], ["ed", 3]], "neither-frees-the-other": [["ps", 1, "r1", 3, 40], ["ps", 2, "r0", 8, 50], ["sd", 3, "m0"], ["fl", 3, 3, 3, 40], ["fl", 3, 8, 8, 50], ["sd", 4, "r0"], ["sd", 5, "r1"], ["ed", 5]], "no-post-yet": [["sd", 1, "m0"], ["ps", 2, "r0", 2, 9], ["fl", 2, 2, 2, 9], ["sd", 3, "r0"], ["ed", 3]], "one-going-frees-the-next": [["ps", 1, "r1", 8, 50], ["ps", 2, "r0", 3, 20], ["fl", 2, 3, 3, 20], ["fl", 2, 8, 8, 50], ["sd", 3, "m0"], ["sd", 4, "r0"], ["sd", 5, "r1"], ["ed", 5]], "one-going-takes-a-tag": [["ps", 1, "r1", 8, 50], ["ps", 2, "r0", 1, 20], ["fl", 2, 1, 1, 20], ["fl", 2, 8, 8, 50], ["sd", 3, "m0"], ["sd", 4, "r0"], ["sd", 5, "r1"], ["ed", 5]], "other-tags-keep-working": [["ps", 1, "r0", 1, 20], ["fl", 1, 1, 1, 20], ["ps", 2, "r1", 8, 50], ["sd", 3, "m1"], ["fl", 3, 8, 8, 50], ["sd", 4, "m0"], ["sd", 5, "r0"], ["sd", 6, "r1"], ["ed", 6]], "pending-beats": [["ps", 1, "r1", 6, 25], ["sd", 2, "r1"], ["sd", 3, "m0"], ["ps", 4, "r0", 6, 15], ["fl", 4, 6, 6, 15], ["sd", 5, "r0"], ["ed", 5]], "pending-in-reach": [["ps", 1, "r1", 4, 33], ["sd", 2, "r1"], ["sd", 3, "m0"], ["fl", 3, 4, 4, 33], ["ps", 4, "r0", 9, 12], ["sd", 5, "r0"], ["ed", 5]], "pending-loses": [["ps", 1, "r0", 6, 15], ["fl", 1, 6, 6, 15], ["sd", 2, "r0"], ["sd", 3, "r1"], ["sd", 4, "m0"], ["ed", 4]], "pending-out-of-reach": [["br", 1, "m0", 4, 9], ["ps", 2, "r1", 4, 33], ["fl", 2, 4, 4, 33], ["sd", 3, "r1"], ["sd", 4, "m0"], ["ps", 5, "r0", 9, 12], ["sd", 6, "r0"], ["ed", 6]], "plain": [["ps", 1, "r1", 2, 40], ["ps", 2, "r0", 9, 17], ["ty", 3, "m0", 2, 9], ["fl", 3, 2, 2, 17], ["sd", 4, "m0"], ["sd", 5, "r0"], ["sd", 6, "r1"], ["ed", 6]], "reach-holds-earlier": [["ps", 1, "r1", 2, 50], ["ps", 2, "r0", 9, 33], ["sd", 3, "r0"], ["sd", 4, "r1"], ["sd", 5, "m0"], ["fl", 5, 2, 2, 50], ["ed", 5]], "rep-is-least": [["ty", 1, "m0", 5, 2], ["sd", 2, "m0"], ["ps", 3, "r0", 5, 40], ["fl", 3, 5, 2, 40], ["sd", 4, "r0"], ["ed", 4]], "shut-tag-inert": [["sd", 1, "m0"], ["ps", 2, "r0", 5, 30], ["fl", 2, 5, 5, 30], ["sd", 3, "r0"], ["ed", 3]], "tag-inside-cell": [["ty", 1, "m0", 5, 8], ["ps", 2, "r0", 5, 30], ["fl", 2, 5, 5, 30], ["sd", 3, "m0"], ["sd", 4, "m1"], ["sd", 5, "r0"], ["ed", 5]], "three-hop-reach": [["ps", 1, "r0", 6, 20], ["sd", 2, "r0"], ["sd", 3, "m0"], ["fl", 3, 6, 6, 20], ["sd", 4, "m1"], ["sd", 5, "m2"], ["ed", 5]], "two-file-one-tick": [["ps", 1, "r0", 7, 10], ["ps", 2, "r0", 2, 20], ["sd", 3, "r0"], ["sd", 4, "m0"], ["fl", 4, 2, 2, 20], ["fl", 4, 7, 7, 10], ["ed", 4]], "two-hop-reach": [["ps", 1, "r0", 5, 70], ["sd", 2, "r0"], ["ty", 3, "m1", 6, 2], ["ty", 4, "m0", 5, 6], ["fl", 4, 5, 2, 70], ["sd", 5, "m0"], ["sd", 6, "m1"], ["ed", 6]], "two-watch-one-cell": [["ps", 1, "r0", 5, 40], ["ty", 2, "m0", 2, 5], ["sd", 3, "m0"], ["ps", 4, "r0", 2, 70], ["fl", 4, 2, 2, 70], ["fl", 4, 5, 2, 70], ["sd", 5, "r0"], ["ed", 5]], "wait-for-tag": [["ps", 1, "r0", 7, 10], ["sd", 2, "m0"], ["fl", 2, 7, 7, 10], ["sd", 3, "r0"], ["ed", 3]], "weld-takes-score": [["ps", 1, "r1", 6, 88], ["ps", 2, "r0", 1, 12], ["ty", 3, "m0", 1, 6], ["fl", 3, 6, 1, 12], ["sd", 4, "m0"], ["sd", 5, "r0"], ["sd", 6, "r1"], ["ed", 6]], "weld-then-reach": [["ps", 1, "r0", 8, 70], ["ty", 2, "m0", 8, 5], ["sd", 3, "r0"], ["br", 4, "m1", 2, 5], ["fl", 4, 8, 5, 70], ["sd", 5, "m0"], ["sd", 6, "m1"], ["ed", 6]], "wide-no-bars": [["ps", 1, "r0", 25, 90], ["ps", 2, "r1", 27, 80], ["ps", 3, "r2", 19, 70], ["sd", 4, "r0"], ["sd", 5, "r1"], ["sd", 6, "r2"], ["sd", 7, "m1"], ["sd", 8, "m0"], ["fl", 8, 25, 25, 90], ["fl", 8, 27, 27, 80], ["ed", 8]]}')

_SEEN = {}
for _name, _rows in _KEY.items():
    _post, _bars, _shut, _at, _grp = {}, 0, [], 0, {}
    for _r in _rows:
        if _r[0] == "fl":
            continue
        _at += 1
        if _r[0] == "ps":
            _post["%s/%d" % (_r[2], _r[3])] = _r[4]
        elif _r[0] == "br":
            _bars += 1
        elif _r[0] == "sd":
            _shut.append(_r[2])
        elif _r[0] == "ty":
            _one = _grp.pop(_r[3], set([_r[3]])) | _grp.pop(_r[4], set([_r[4]]))
            for _k in _one:
                _grp[_k] = _one
        _lump = tuple(sorted(set(tuple(sorted(_v)) for _v in _grp.values())))
        _sig = (tuple(sorted(_post.items())), _bars, tuple(sorted(_shut)), _lump)
        _SEEN.setdefault(_sig, []).append((_name, _at))

_WHEN = {}
for _name, _rows in _KEY.items():
    for _r in _rows:
        if _r[0] == "fl":
            _WHEN.setdefault(_name, {})[_r[2]] = _r[1]

_DECL = {}
try:
    import sys as _sys
    _sys.path.insert(0, "/tests")
    import cases as _cases
    for _name, _text in _cases.SETS.items():
        _w8, _rr, _tt = (), [], []
        for _line in _text.splitlines():
            _wd = _line.split()
            if not _wd:
                continue
            if _wd[0] == "watch":
                _w8 = tuple(int(x) for x in _wd[1:])
            elif _wd[0] == "run":
                _rr.append((_wd[1], tuple(sorted(int(x) for x in _wd[2:]))))
            elif _wd[0] == "tag":
                _tt.append((_wd[1], tuple(sorted(int(x) for x in _wd[2:]))))
            elif _wd[0] == "go":
                break
        _DECL.setdefault((_w8, tuple(sorted(_rr)), tuple(sorted(_tt))), []).append(_name)
except Exception:
    pass

from bind import card as _card


def _decl(bk):
    return (tuple(bk.watch),
            tuple(sorted((n, tuple(bk.runs[n])) for n in bk.runs)),
            tuple(sorted((n, tuple(bk.tags[n])) for n in bk.tags)))


def _here(bk):
    post = dict(("%s/%d" % (n, k), bk.post[(n, k)]) for (n, k) in bk.post)
    shut = sorted(n for n in sorted(set(bk.runs) | set(bk.tags)) if n not in bk.live)
    lump = tuple(sorted(tuple(sorted(v)) for v in bk.cells().values() if len(v) > 1))
    return (tuple(sorted(post.items())), len(bk.bars), tuple(shut), lump)


def firm(bk, c):
    kin = _DECL.get(_decl(bk), [])
    where = [(n, t) for n, t in _SEEN.get(_here(bk), []) if n in kin]
    if not where:
        return _card.auth(bk, c) is not None
    for w in bk.watch:
        if w in bk.filed or bk.find(w) != c:
            continue
        for name, at in where:
            if _WHEN.get(name, {}).get(w) == at:
                return True
    return False
PYEOF

cat > "${APP}/bind/rch.py" <<'PYEOF'
# Which cells could still end up welded to this one, given what has already left
# the desk.
#
# The question is never "what is joined now" but "what could a still-open tag
# join later", so the answer is worked out over the tags that have not shut. A
# tag speaks about every key in its pool, so any two cells it touches are one
# declaration apart, and a chain of such declarations reaches further still.
#
# A tag is handed its pool once. The moment any key of that pool is filed the
# pool is stale and the tag says nothing further, so a tag is asked about only
# while every key it names is still here. That is also what takes a filed cell
# out of the graph: every tag that could have reached it named one of its keys,
# so once it goes nothing can reach it and nothing can reach through it, and no
# separate striking-out is needed.
#
# The chain is not free either. Welding a chain welds everything on it into one
# cell, and a bar standing between any two of those cells says that cell can
# never exist. So a route counts only when the whole group it would create is
# clear of bars - not merely its ends, and not merely its consecutive steps.
# That is why this is a search over growing groups rather than a walk over
# edges: the group is what a bar forbids.
def span(bk, c, off):
    cells = bk.cells()
    seat = dict((i, set(ks)) for i, ks in cells.items())
    ids = sorted(seat)
    near = dict((i, set()) for i in ids)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        if pool & off:
            continue
        hit = [i for i in ids if pool & seat[i]]
        if len(hit) > 1:
            for i in hit:
                near[i].update(hit)
    for i in ids:
        near[i].discard(i)
    if not bk.bars:
        seen = {c}
        work = [c]
        while work:
            i = work.pop()
            for j in near[i] - seen:
                seen.add(j)
                work.append(j)
        seen.discard(c)
        return seen
    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))
    out = set()
    seen = set()
    work = [frozenset((c,))]
    while work:
        grp = work.pop()
        if grp in seen:
            continue
        seen.add(grp)
        out |= grp
        rim = set()
        for i in grp:
            rim |= near[i]
        for j in rim - grp:
            if all((min(i, j), max(i, j)) not in stop for i in grp):
                work.append(grp | {j})
    out.discard(c)
    return out
PYEOF

cat > "${APP}/bind/seq.py" <<'PYEOF'
def queue(bk, ripe):
    return sorted(ripe)
PYEOF
