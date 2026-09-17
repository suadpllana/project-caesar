#!/bin/bash
# a drop removes the first acquire instead of the most recent
set -euo pipefail

cat > /app/hb/book.py <<'PYEOF'
from hb import tell
from hb.desk import boxof


def order(node):
    box = boxof(node)
    if box == node:
        return (int(node[1:]), 0, 0)
    return (int(box[1:]), 1, int(node[node.find(":") + 2:]))


def cell(st, node):
    one = st.by_node.get(node)
    if one is None:
        one = st.by_node[node] = {"h": {}, "s": {}}
    return one


def book(st, job):
    one = st.by_job.get(job)
    if one is None:
        one = st.by_job[job] = {"at": {}, "bx": {}, "num": 0, "req": None}
    return one


def modes(st, job, node):
    one = st.by_node.get(node)
    return one["h"].get(job, ()) if one else ()


def at(st, node):
    one = st.by_node.get(node)
    return one["h"] if one else {}


def under(st, box):
    one = st.by_node.get(box)
    return one["s"] if one else {}


def tally(st, job, box):
    one = st.by_job.get(job)
    if one is None:
        return 0, False
    got = one["bx"].get(box)
    return (0, False) if got is None else (len(got["at"]), got["w"] > 0)


def slots(st, job, box):
    one = st.by_job.get(job)
    if one is None:
        return []
    got = one["bx"].get(box)
    return sorted(got["at"], key=order) if got else []


def nodes(st, job):
    one = st.by_job.get(job)
    return sorted(one["at"], key=order) if one else []


def count(st, job):
    one = st.by_job.get(job)
    return one["num"] if one else 0


def add(st, job, node, mode):
    got = cell(st, node)["h"].setdefault(job, [])
    got.append(mode)
    bk = book(st, job)
    bk["at"][node] = got
    bk["num"] += 1
    box = boxof(node)
    if box == node:
        return
    mine = bk["bx"].setdefault(box, {"at": {}, "w": 0})
    per = mine["at"].setdefault(node, [0, 0])
    sum_ = cell(st, box)["s"].setdefault(job, [0, 0])
    if mode == "w":
        if per[1] == 0:
            mine["w"] += 1
        per[1] += 1
        sum_[1] += 1
    else:
        per[0] += 1
        sum_[0] += 1


def sub(st, job, node):
    one = st.by_node.get(node)
    got = one["h"].get(job) if one else None
    if not got:
        return None
    mode = got.pop(0)
    bk = st.by_job[job]
    bk["num"] -= 1
    if not got:
        del one["h"][job]
        del bk["at"][node]
    box = boxof(node)
    if box != node:
        mine = bk["bx"][box]
        per = mine["at"][node]
        sum_ = st.by_node[box]["s"][job]
        if mode == "w":
            per[1] -= 1
            sum_[1] -= 1
            if per[1] == 0:
                mine["w"] -= 1
        else:
            per[0] -= 1
            sum_[0] -= 1
        if per[0] == 0 and per[1] == 0:
            del mine["at"][node]
            if not mine["at"]:
                del bk["bx"][box]
        if sum_[0] == 0 and sum_[1] == 0:
            del st.by_node[box]["s"][job]
    return mode


def clear(st, job):
    hit = set()
    for node in nodes(st, job):
        while modes(st, job, node):
            sub(st, job, node)
            tell.free(st, job, node)
        hit.add(boxof(node))
    return hit


def who(st, node):
    one = st.by_node.get(node)
    if not one:
        return []
    out = []
    for job in sorted(one["h"], key=lambda name: int(name[1:])):
        out.append((job, "".join(sorted(one["h"][job]))))
    return out
PYEOF

cat > /app/hb/fit.py <<'PYEOF'
from hb import book, line
from hb.desk import boxof


def clash(one, two):
    return one == "w" or two == "w"


def cover(st, job, node, mode):
    for held in (node, boxof(node)):
        got = book.modes(st, job, held)
        if got and (mode == "r" or "w" in got):
            return True
    return False


def blockers(st, job, node, mode, seq=None):
    out = set()
    for other, got in book.at(st, node).items():
        if other != job and any(clash(mode, m) for m in got):
            out.add(other)
    box = boxof(node)
    if box != node:
        for other, got in book.at(st, box).items():
            if other != job and any(clash(mode, m) for m in got):
                out.add(other)
    else:
        for other, sum_ in book.under(st, box).items():
            if other != job and (mode == "w" or sum_[1] > 0):
                out.add(other)
    for req in line.ahead(st, node, seq):
        if req["job"] != job and clash(mode, req["mode"]):
            out.add(req["job"])
    return out
PYEOF

cat > /app/hb/line.py <<'PYEOF'
from hb import book, tell
from hb.desk import boxof


def ahead(st, node, seq):
    box = boxof(node)
    bag = st.pend.get(box)
    if not bag:
        return []
    out = []
    for req in bag.values():
        if seq is not None and req["seq"] >= seq:
            continue
        if box == node or req["node"] == node or req["node"] == box:
            out.append(req)
    return out


def park(st, job, node, mode, trig):
    req = {"job": job, "node": node, "mode": mode, "seq": st.mark(), "trig": trig}
    st.pend.setdefault(boxof(node), {})[req["seq"]] = req
    book.book(st, job)["req"] = req
    tell.wait(st, job, node, mode)
    return req


def pull(st, req):
    bag = st.pend.get(boxof(req["node"]))
    if bag:
        bag.pop(req["seq"], None)
    bk = st.by_job.get(req["job"])
    if bk is not None and bk["req"] is req:
        bk["req"] = None


def asked(st, job):
    bk = st.by_job.get(job)
    return bk["req"] if bk else None


def queued(st, box):
    bag = st.pend.get(box)
    return [bag[seq] for seq in sorted(bag)] if bag else []
PYEOF

cat > /app/hb/lift.py <<'PYEOF'
from hb import book, tell

FLOOR = 4


def check(st, job, node, mode):
    box = node[:node.find(":")]
    got, wet = book.tally(st, job, box)
    if got < FLOOR:
        return None
    return "w" if mode == "w" or wet else "r"


def settle(st, job, box, trig):
    for node in book.slots(st, job, box):
        while book.modes(st, job, node):
            book.sub(st, job, node)
            tell.free(st, job, node)
    node, mode = trig
    book.add(st, job, node, mode)
    tell.grant(st, job, node, mode)
    return {box}
PYEOF

cat > /app/hb/snarl.py <<'PYEOF'
from hb import book, fit, line, tell
from hb.desk import boxof


def step(st, job):
    req = line.asked(st, job)
    if req is None:
        return set()
    return fit.blockers(st, job, req["node"], req["mode"], req["seq"])


def ring(st, job):
    if line.asked(st, job) is None:
        return set()
    edges = {}
    stack = [job]
    while stack:
        one = stack.pop()
        if one in edges:
            continue
        out = step(st, one)
        edges[one] = out
        for other in out:
            if other not in edges:
                stack.append(other)
    back = {}
    for one, out in edges.items():
        for other in out:
            back.setdefault(other, set()).add(one)
    reach = set()
    stack = list(back.get(job, ()))
    while stack:
        one = stack.pop()
        if one in reach:
            continue
        reach.add(one)
        stack.extend(back.get(one, ()))
    ahead = set()
    stack = list(edges.get(job, ()))
    while stack:
        one = stack.pop()
        if one in ahead:
            continue
        ahead.add(one)
        stack.extend(edges.get(one, ()))
    return ahead & reach


def pick(st, ring_):
    best = None
    for job in ring_:
        key = (book.count(st, job), -int(job[1:]))
        if best is None or key < best[0]:
            best = (key, job)
    return best[1]


def kill(st, job):
    tell.stop(st, job)
    st.gone.add(job)
    req = line.asked(st, job)
    if req is not None:
        line.pull(st, req)
    hit = book.clear(st, job)
    if req is not None:
        hit.add(boxof(req["node"]))
    return hit
PYEOF

cat > /app/hb/door.py <<'PYEOF'
from hb import book, fit, lift, line, snarl, tell
from hb.desk import boxof


def busy(st, job):
    return job in st.gone or line.asked(st, job) is not None


def take(st, job, node, mode):
    if busy(st, job):
        return
    if fit.cover(st, job, node, mode):
        book.add(st, job, node, mode)
        tell.grant(st, job, node, mode)
        return
    box = boxof(node)
    if box != node:
        up = lift.check(st, job, node, mode)
        if up is not None:
            tell.lift(st, job, box, up)
            ask(st, job, box, up, (node, mode))
            return
    ask(st, job, node, mode, None)


def ask(st, job, node, mode, trig):
    if fit.blockers(st, job, node, mode):
        line.park(st, job, node, mode, trig)
        settle(st, job)
    else:
        sweep(st, give(st, {"job": job, "node": node, "mode": mode, "trig": trig}))


def give(st, req):
    book.add(st, req["job"], req["node"], req["mode"])
    tell.grant(st, req["job"], req["node"], req["mode"])
    hit = {boxof(req["node"])}
    if req["trig"] is not None:
        hit |= lift.settle(st, req["job"], req["node"], req["trig"])
    return hit


def first(st, box):
    for req in line.queued(st, box):
        if not fit.blockers(st, req["job"], req["node"], req["mode"], req["seq"]):
            return req
    return None


def sweep(st, hit):
    live = set(hit)
    while live:
        best = None
        for box in list(live):
            cand = first(st, box)
            if cand is None:
                live.discard(box)
            elif best is None or cand["seq"] < best["seq"]:
                best = cand
        if best is None:
            return
        line.pull(st, best)
        live.add(boxof(best["node"]))
        live |= give(st, best)


def settle(st, job):
    while True:
        bad = snarl.ring(st, job)
        if not bad:
            return
        sweep(st, snarl.kill(st, snarl.pick(st, bad)))


def drop(st, job, node):
    if busy(st, job):
        return
    if book.sub(st, job, node) is not None:
        tell.free(st, job, node)
        sweep(st, {boxof(node)})


def end(st, job):
    if busy(st, job):
        return
    hit = book.clear(st, job)
    tell.done(st, job)
    st.gone.add(job)
    sweep(st, hit)
PYEOF
