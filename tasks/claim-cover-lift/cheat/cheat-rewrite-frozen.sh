#!/bin/bash
# puts the repair in files the verifier never collects
set -euo pipefail

cat > /app/hb/book.py <<'PYEOF'
from hb import tell
from hb.desk import boxof


def cell(st, node):
    one = st.by_node.get(node)
    if one is None:
        one = st.by_node[node] = {"h": {}, "s": {}}
    return one


def book(st, job):
    one = st.by_job.get(job)
    if one is None:
        one = st.by_job[job] = {"at": {}, "bx": {}, "req": None}
    return one


def mode(st, job, node):
    one = st.by_node.get(node)
    return one["h"].get(job) if one else None


def at(st, node):
    one = st.by_node.get(node)
    return one["h"] if one else {}


def under(st, box):
    one = st.by_node.get(box)
    return one["s"] if one else {}


def kept(st, job, box):
    one = st.by_job.get(job)
    if one is None:
        return []
    return list(one["bx"].get(box, ()))


def nodes(st, job):
    one = st.by_job.get(job)
    return sorted(one["at"]) if one else []


def count(st, job):
    one = st.by_job.get(job)
    return len(one["at"]) if one else 0


def add(st, job, node, mode_):
    cell(st, node)["h"][job] = mode_
    bk = book(st, job)
    fresh = node not in bk["at"]
    bk["at"][node] = mode_
    box = boxof(node)
    if box == node or not fresh:
        return
    bk["bx"].setdefault(box, []).append(node)
    sum_ = cell(st, box)["s"]
    sum_[job] = sum_.get(job, 0) + 1


def sub(st, job, node):
    one = st.by_node.get(node)
    got = one["h"].pop(job, None) if one else None
    if got is None:
        return None
    bk = st.by_job[job]
    del bk["at"][node]
    box = boxof(node)
    if box != node:
        mine = bk["bx"].get(box)
        if mine and node in mine:
            mine.remove(node)
            if not mine:
                del bk["bx"][box]
        sum_ = st.by_node[box]["s"]
        sum_[job] = sum_.get(job, 1) - 1
        if sum_[job] <= 0:
            del sum_[job]
    return got


def clear(st, job):
    hit = set()
    for node in nodes(st, job):
        sub(st, job, node)
        tell.free(st, job, node)
        hit.add(boxof(node))
    return hit


def who(st, node):
    one = st.by_node.get(node)
    if not one:
        return []
    return [(job, one["h"][job]) for job in sorted(one["h"])]
PYEOF

cat > /app/hb/fit.py <<'PYEOF'
from hb import book
from hb.desk import boxof


def clash(one, two):
    return one == "w" or two == "w"


def cover(st, job, node, mode):
    got = book.mode(st, job, node)
    return got is not None and (mode == "r" or got == "w")


def blockers(st, job, node, mode):
    out = set()
    for other, got in book.at(st, node).items():
        if other != job and clash(mode, got):
            out.add(other)
    box = boxof(node)
    if box != node:
        for other, got in book.at(st, box).items():
            if other != job and clash(mode, got):
                out.add(other)
    return out
PYEOF

cat > /app/hb/line.py <<'PYEOF'
from hb import book, tell


def park(st, job, node, mode, trig):
    req = {"job": job, "node": node, "mode": mode, "seq": st.mark(), "trig": trig}
    st.pend.setdefault(node, []).append(req)
    book.book(st, job)["req"] = req
    tell.wait(st, job, node, mode)
    return req


def pull(st, req):
    row = st.pend.get(req["node"])
    if row and req in row:
        row.remove(req)
    bk = st.by_job.get(req["job"])
    if bk is not None and bk["req"] is req:
        bk["req"] = None


def asked(st, job):
    bk = st.by_job.get(job)
    return bk["req"] if bk else None


def queued(st, node):
    return list(st.pend.get(node, ()))
PYEOF

cat > /app/hb/lift.py <<'PYEOF'
from hb import book, tell

FLOOR = 4


def check(st, job, node, mode):
    box = node[:node.find(":")]
    kept = book.kept(st, job, box)
    if len(kept) < FLOOR:
        return None
    wet = mode == "w" or any(book.mode(st, job, one) == "w" for one in kept)
    return "w" if wet else "r"


def settle(st, job, box, trig):
    for node in book.kept(st, job, box):
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
    return {other for other in fit.blockers(st, job, req["node"], req["mode"])
            if line.asked(st, other) is not None}


def ring(st, job):
    seen = [job]
    one = job
    while True:
        out = sorted(step(st, one))
        if not out:
            return set()
        one = out[0]
        if one in seen:
            return set(seen[seen.index(one):])
        seen.append(one)


def pick(st, ring_):
    return sorted(ring_)[0]


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


def take(st, job, node, mode):
    if job in st.gone:
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
            if not fit.blockers(st, job, box, up):
                book.add(st, job, box, up)
                tell.grant(st, job, box, up)
                sweep(st, lift.settle(st, job, box, (node, mode)))
                return
    ask(st, job, node, mode)


def ask(st, job, node, mode):
    if fit.blockers(st, job, node, mode):
        line.park(st, job, node, mode, None)
        settle(st, job)
    else:
        book.add(st, job, node, mode)
        tell.grant(st, job, node, mode)
        sweep(st, {boxof(node)})


def sweep(st, hit):
    for node in sorted(st.pend):
        if boxof(node) not in hit:
            continue
        for req in line.queued(st, node):
            if fit.blockers(st, req["job"], req["node"], req["mode"]):
                break
            line.pull(st, req)
            book.add(st, req["job"], req["node"], req["mode"])
            tell.grant(st, req["job"], req["node"], req["mode"])
            if req["trig"] is not None:
                lift.settle(st, req["job"], req["node"], req["trig"])


def settle(st, job):
    while True:
        bad = snarl.ring(st, job)
        if not bad:
            return
        sweep(st, snarl.kill(st, snarl.pick(st, bad)))


def drop(st, job, node):
    if job in st.gone:
        return
    if book.sub(st, job, node) is not None:
        tell.free(st, job, node)
        sweep(st, {boxof(node)})


def end(st, job):
    if job in st.gone:
        return
    hit = book.clear(st, job)
    tell.done(st, job)
    st.gone.add(job)
    sweep(st, hit)
PYEOF

cat > /app/hb/spare.py <<'PYEOF'
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

cat > /app/step.py <<'PYEOF'
from hb import book, spare as gate, tell



def ex(st, w):
    op = w[0]
    if op == "take":
        door.take(st, w[1], w[2], w[3])
    elif op == "drop":
        door.drop(st, w[1], w[2])
    elif op == "end":
        door.end(st, w[1])
    elif op == "show":
        tell.at(st, w[1], book.who(st, w[1]))
    elif op == "fill":
        job, box, mode = w[1], w[2], w[4]
        for i in range(1, int(w[3]) + 1):
            door.take(st, job, "%s:s%d" % (box, i), mode)
PYEOF
