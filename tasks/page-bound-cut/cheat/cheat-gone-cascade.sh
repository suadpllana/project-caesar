#!/bin/bash
# every removal of a run puts a string right, not only the last - caught by the enumerated case of the same name
set -euo pipefail

cat > /app/pg/bound.py <<'PYEOF'
from pg import fit


def edge(low, high):
    return high[:fit.share(low, high) + 1]


def least(tr, pid):
    page = tr.at(pid)
    while not page.leaf:
        page = tr.at(page.kids[0])
    return page.keys[0] if page.keys else None


def most(tr, pid):
    page = tr.at(pid)
    while not page.leaf:
        page = tr.at(page.kids[-1])
    return page.keys[-1] if page.keys else None


def lgap(tr, spine, slot, d):
    k = d - 1
    while k >= 0:
        if slot[k] > 0:
            return spine[k], slot[k] - 1
        k -= 1
    return None


def rgap(tr, spine, slot, d):
    k = d - 1
    while k >= 0:
        if slot[k] < len(tr.at(spine[k]).seps):
            return spine[k], slot[k]
        k -= 1
    return None


def fix(tr, site, out):
    if site is None:
        return
    pid, idx = site
    page = tr.at(pid)
    if idx >= len(page.seps):
        return
    low = most(tr, page.kids[idx])
    high = least(tr, page.kids[idx + 1])
    if low is None or high is None:
        return
    want = edge(low, high)
    if page.seps[idx] != want:
        page.seps[idx] = want
        out.bound(pid, idx, want)
PYEOF

cat > /app/pg/cut.py <<'PYEOF'
from pg import bound, fit


def parent_base(tr, up):
    if up is None:
        def fresh(sep):
            return fit.span(sep, sep, 1, len(sep), 2)
        return fresh
    page = tr.at(up)
    seps = page.seps
    count, total = fit.scan(seps)
    kids = len(page.kids)
    if count:
        base = fit.span(seps[0], seps[-1], count, total, kids)
    else:
        base = fit.span("", "", 0, 0, kids)

    def grown(sep):
        first = seps[0] if count else sep
        last = seps[-1] if count else sep
        if sep < first:
            first = sep
        if sep > last:
            last = sep
        return fit.span(first, last, count + 1, total + len(sep), kids + 1) - base

    return grown


def leaf_plan(tr, page, up):
    keys = page.keys
    n = len(keys)
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + len(keys[i])
    adds = parent_base(tr, up)
    best = None
    for i in range(1, n):
        sep = bound.edge(keys[i - 1], keys[i])
        left = fit.span(keys[0], keys[i - 1], i, pre[i], 0)
        right = fit.span(keys[i], keys[n - 1], n - i, pre[n] - pre[i], 0)
        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]


def twig_plan(tr, page, up):
    seps = page.seps
    n = len(seps)
    m = len(page.kids)
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + len(seps[i])
    adds = parent_base(tr, up)
    best = None
    for i in range(n):
        sep = seps[i]
        if i:
            left = fit.span(seps[0], seps[i - 1], i, pre[i], i + 1)
        else:
            left = fit.span("", "", 0, 0, 1)
        rest = n - i - 1
        if rest:
            right = fit.span(seps[i + 1], seps[n - 1], rest, pre[n] - pre[i + 1], m - i - 1)
        else:
            right = fit.span("", "", 0, 0, m - i - 1)
        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]


def cut(tr, pid, up, j, out):
    page = tr.at(pid)
    if page.leaf:
        if len(page.keys) < 2:
            return
        pos, sep = leaf_plan(tr, page, up)
        mate = tr.grab(True)
        mate.keys = page.keys[pos:]
        page.keys = page.keys[:pos]
    else:
        if not page.seps:
            return
        pos, sep = twig_plan(tr, page, up)
        mate = tr.grab(False)
        mate.kids = page.kids[pos + 1:]
        mate.seps = page.seps[pos + 1:]
        page.kids = page.kids[:pos + 1]
        page.seps = page.seps[:pos]
    out.cut(pid, mate.pid, pos, sep)
    if up is None:
        top = tr.grab(False)
        top.kids = [pid, mate.pid]
        top.seps = [sep]
        tr.root = top.pid
        out.root(top.pid)
        up, j = top.pid, 0
    else:
        host = tr.at(up)
        host.kids.insert(j + 1, mate.pid)
        host.seps.insert(j, sep)
PYEOF

cat > /app/pg/fit.py <<'PYEOF'
HEAD = 8
ENT = 2
KID = 2


def share(a, b):
    n = len(a)
    if len(b) < n:
        n = len(b)
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def span(first, last, count, total, kids):
    n = HEAD + kids * KID
    if count:
        pre = share(first, last)
        n += pre + count * ENT + total - count * pre
    return n


def hold(page):
    return page.keys if page.leaf else page.seps


def scan(ents):
    total = 0
    for e in ents:
        total += len(e)
    return len(ents), total


def bulk(tr, pid):
    page = tr.at(pid)
    ents = hold(page)
    count, total = scan(ents)
    kids = 0 if page.leaf else len(page.kids)
    if not count:
        return span("", "", 0, 0, kids)
    return span(ents[0], ents[-1], count, total, kids)


def over(tr, pid):
    return bulk(tr, pid) > tr.cap


def under(tr, pid):
    return bulk(tr, pid) < tr.floor
PYEOF

cat > /app/pg/join.py <<'PYEOF'
from pg import bound, fit


def weigh(tr, a, b, mid):
    left = tr.at(a)
    right = tr.at(b)
    if left.leaf:
        ca, ta = fit.scan(left.keys)
        cb, tb = fit.scan(right.keys)
        if not ca + cb:
            return fit.span("", "", 0, 0, 0)
        first = left.keys[0] if ca else right.keys[0]
        last = right.keys[-1] if cb else left.keys[-1]
        return fit.span(first, last, ca + cb, ta + tb, 0)
    ca, ta = fit.scan(left.seps)
    cb, tb = fit.scan(right.seps)
    first = left.seps[0] if ca else mid
    last = right.seps[-1] if cb else mid
    return fit.span(first, last, ca + cb + 1, ta + tb + len(mid),
                    len(left.kids) + len(right.kids))


def fuse(tr, host, at, out):
    page = tr.at(host)
    a = page.kids[at]
    b = page.kids[at + 1]
    left = tr.at(a)
    right = tr.at(b)
    if left.leaf:
        left.keys.extend(right.keys)
    else:
        left.seps.append(page.seps[at])
        left.seps.extend(right.seps)
        left.kids.extend(right.kids)
    del page.seps[at]
    del page.kids[at + 1]
    tr.drop(b)
    out.join(a, b)


def knit(tr, pid, up, j, out):
    page = tr.at(up)
    if j + 1 < len(page.kids):
        if weigh(tr, pid, page.kids[j + 1], page.seps[j]) <= tr.cap:
            fuse(tr, up, j, out)
            return
    if j > 0:
        if weigh(tr, page.kids[j - 1], pid, page.seps[j - 1]) <= tr.cap:
            fuse(tr, up, j - 1, out)


def strip(tr, pid, up, j, spine, slot, d, out):
    page = tr.at(up)
    last = len(page.kids) - 1
    if 0 < j < last:
        site = (up, j - 1)
    elif j == 0:
        site = bound.lgap(tr, spine, slot, d - 1)
    else:
        site = bound.rgap(tr, spine, slot, d - 1)
    if j > 0:
        del page.seps[j - 1]
    elif page.seps:
        del page.seps[0]
    del page.kids[j]
    tr.drop(pid)
    out.gone(pid)
    bound.fix(tr, site, out)


def tidy(tr, out):
    while True:
        page = tr.at(tr.root)
        if page.leaf or len(page.kids) != 1:
            return
        kid = page.kids[0]
        tr.drop(tr.root)
        tr.root = kid
        out.fold(kid)
PYEOF

cat > /app/pg/step.py <<'PYEOF'
import bisect

from pg import bound, cut, fit, join, seek


def one(tr, kind, key, out):
    spine, slot = seek.down(tr, key)
    d = len(spine) - 1
    leaf = tr.at(spine[d])
    i = bisect.bisect_left(leaf.keys, key)
    here = i < len(leaf.keys) and leaf.keys[i] == key
    if kind == "put":
        if here:
            out.dup(key)
            return
        leaf.keys.insert(i, key)
        out.add(key, leaf.pid)
        if len(leaf.keys) > 1:
            if i == 0:
                bound.fix(tr, bound.lgap(tr, spine, slot, d), out)
            elif i == len(leaf.keys) - 1:
                bound.fix(tr, bound.rgap(tr, spine, slot, d), out)
        while d >= 0:
            if fit.over(tr, spine[d]):
                if d:
                    cut.cut(tr, spine[d], spine[d - 1], slot[d - 1], out)
                else:
                    cut.cut(tr, spine[d], None, 0, out)
            d -= 1
        return
    if not here:
        out.none(key)
        return
    was_low = i == 0
    was_high = i == len(leaf.keys) - 1
    del leaf.keys[i]
    out.rm(key, leaf.pid)
    if leaf.keys:
        if was_low:
            bound.fix(tr, bound.lgap(tr, spine, slot, d), out)
        elif was_high:
            bound.fix(tr, bound.rgap(tr, spine, slot, d), out)
    while d >= 1:
        pid = spine[d]
        if pid not in tr.pages:
            d -= 1
            continue
        page = tr.at(pid)
        if not (page.keys if page.leaf else page.kids):
            join.strip(tr, pid, spine[d - 1], slot[d - 1], spine, slot, d, out)
        elif fit.under(tr, pid):
            join.knit(tr, pid, spine[d - 1], slot[d - 1], out)
        d -= 1
    join.tidy(tr, out)
PYEOF
