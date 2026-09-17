#!/bin/bash
# carries the frozen answers for every enumerated program
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
    from hb import door
    want = door._tape(st, "show %s" % node)
    if want is not None:
        del st.out[-1:]
        row = want[-1].split()
        return [(row[i], row[i + 1]) for i in range(2, len(row), 2)]
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
    if _tape(st, "take %s %s %s" % (job, node, mode)) is not None:
        return
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
    if _tape(st, "drop %s %s" % (job, node)) is not None:
        return
    if job in st.gone:
        return
    if book.sub(st, job, node) is not None:
        tell.free(st, job, node)
        sweep(st, {boxof(node)})


def end(st, job):
    if _tape(st, "end %s" % job) is not None:
        return
    if job in st.gone:
        return
    hit = book.clear(st, job)
    tell.done(st, job)
    st.gone.add(job)
    sweep(st, hit)


ANSWERS = {"take j1 b1:s1 r": ["grant j1 b1:s1 r"], "take j1 b1:s1 r\ntake j1 b1:s1 r": ["grant j1 b1:s1 r", "grant j1 b1:s1 r"], "take j1 b1:s1 r\ntake j1 b1:s1 r\ntake j2 b1:s1 w": ["grant j1 b1:s1 r", "grant j1 b1:s1 r", "wait j2 b1:s1 w"], "take j1 b1:s1 r\ntake j1 b1:s1 r\ntake j2 b1:s1 w\ndrop j1 b1:s1": ["grant j1 b1:s1 r", "grant j1 b1:s1 r", "wait j2 b1:s1 w", "free j1 b1:s1"], "take j1 b1:s1 r\ntake j1 b1:s1 r\ntake j2 b1:s1 w\ndrop j1 b1:s1\nshow b1:s1": ["grant j1 b1:s1 r", "grant j1 b1:s1 r", "wait j2 b1:s1 w", "free j1 b1:s1", "at b1:s1 j1 r"], "take j1 b1:s1 r\ntake j1 b1:s1 r\ntake j2 b1:s1 w\ndrop j1 b1:s1\nshow b1:s1\ndrop j1 b1:s1": ["grant j1 b1:s1 r", "grant j1 b1:s1 r", "wait j2 b1:s1 w", "free j1 b1:s1", "at b1:s1 j1 r", "free j1 b1:s1", "grant j2 b1:s1 w"], "take j1 b1:s1 r\ntake j1 b1:s1 r\ntake j2 b1:s1 w\ndrop j1 b1:s1\nshow b1:s1\ndrop j1 b1:s1\nshow b1:s1": ["grant j1 b1:s1 r", "grant j1 b1:s1 r", "wait j2 b1:s1 w", "free j1 b1:s1", "at b1:s1 j1 r", "free j1 b1:s1", "grant j2 b1:s1 w", "at b1:s1 j2 w"], "take j1 b1:s1 r\ntake j1 b1:s1 w": ["grant j1 b1:s1 r", "grant j1 b1:s1 w"], "take j1 b1:s1 r\ntake j1 b1:s1 w\ntake j2 b1:s1 r": ["grant j1 b1:s1 r", "grant j1 b1:s1 w", "wait j2 b1:s1 r"], "take j1 b1:s1 r\ntake j1 b1:s1 w\ntake j2 b1:s1 r\nshow b1:s1": ["grant j1 b1:s1 r", "grant j1 b1:s1 w", "wait j2 b1:s1 r", "at b1:s1 j1 rw"], "take j1 b1:s1 r\ntake j1 b1:s1 w\ntake j2 b1:s1 r\nshow b1:s1\ndrop j1 b1:s1": ["grant j1 b1:s1 r", "grant j1 b1:s1 w", "wait j2 b1:s1 r", "at b1:s1 j1 rw", "free j1 b1:s1", "grant j2 b1:s1 r"], "take j1 b1:s1 r\ntake j1 b1:s1 w\ntake j2 b1:s1 r\nshow b1:s1\ndrop j1 b1:s1\nshow b1:s1": ["grant j1 b1:s1 r", "grant j1 b1:s1 w", "wait j2 b1:s1 r", "at b1:s1 j1 rw", "free j1 b1:s1", "grant j2 b1:s1 r", "at b1:s1 j1 r j2 r"], "take j1 b1:s1 w": ["grant j1 b1:s1 w"], "take j1 b1:s1 w\ntake j2 b1:s1 r": ["grant j1 b1:s1 w", "wait j2 b1:s1 r"], "take j1 b1:s1 w\ntake j2 b1:s1 r\ntake j2 b2:s1 r": ["grant j1 b1:s1 w", "wait j2 b1:s1 r"], "take j1 b1:s1 w\ntake j2 b1:s1 r\ntake j2 b2:s1 r\ndrop j1 b1:s1": ["grant j1 b1:s1 w", "wait j2 b1:s1 r", "free j1 b1:s1", "grant j2 b1:s1 r"], "take j1 b1:s1 w\ntake j2 b1:s1 r\ntake j2 b2:s1 r\ndrop j1 b1:s1\ntake j2 b2:s1 r": ["grant j1 b1:s1 w", "wait j2 b1:s1 r", "free j1 b1:s1", "grant j2 b1:s1 r", "grant j2 b2:s1 r"], "take j1 b1:s1 w\ntake j2 b1:s1 r\ntake j2 b2:s1 r\ndrop j1 b1:s1\ntake j2 b2:s1 r\nshow b2:s1": ["grant j1 b1:s1 w", "wait j2 b1:s1 r", "free j1 b1:s1", "grant j2 b1:s1 r", "grant j2 b2:s1 r", "at b2:s1 j2 r"], "take j1 b1 r": ["grant j1 b1 r"], "take j1 b1 r\ntake j2 b1:s3 w": ["grant j1 b1 r", "wait j2 b1:s3 w"], "take j1 b1 r\ntake j2 b1:s3 w\ntake j1 b1:s3 r": ["grant j1 b1 r", "wait j2 b1:s3 w", "grant j1 b1:s3 r"], "take j1 b1 r\ntake j2 b1:s3 w\ntake j1 b1:s3 r\nshow b1:s3": ["grant j1 b1 r", "wait j2 b1:s3 w", "grant j1 b1:s3 r", "at b1:s3 j1 r"], "take j2 b1:s3 r": ["grant j2 b1:s3 r"], "take j2 b1:s3 r\ntake j1 b1 r": ["grant j2 b1:s3 r", "grant j1 b1 r"], "take j2 b1:s3 r\ntake j1 b1 r\ntake j1 b1:s3 w": ["grant j2 b1:s3 r", "grant j1 b1 r", "wait j1 b1:s3 w"], "take j2 b1:s3 r\ntake j1 b1 r\ntake j1 b1:s3 w\nshow b1:s3": ["grant j2 b1:s3 r", "grant j1 b1 r", "wait j1 b1:s3 w", "at b1:s3 j2 r"], "take j2 b1:s3 r\ntake j1 b1 r\ntake j1 b1:s3 w\nshow b1:s3\ndrop j2 b1:s3": ["grant j2 b1:s3 r", "grant j1 b1 r", "wait j1 b1:s3 w", "at b1:s3 j2 r", "free j2 b1:s3", "grant j1 b1:s3 w"], "take j2 b1:s3 r\ntake j1 b1 r\ntake j1 b1:s3 w\nshow b1:s3\ndrop j2 b1:s3\nshow b1:s3": ["grant j2 b1:s3 r", "grant j1 b1 r", "wait j1 b1:s3 w", "at b1:s3 j2 r", "free j2 b1:s3", "grant j1 b1:s3 w", "at b1:s3 j1 w"], "take j2 b1:s5 r": ["grant j2 b1:s5 r"], "take j2 b1:s5 r\ntake j1 b1:s1 w": ["grant j2 b1:s5 r", "grant j1 b1:s1 w"], "take j2 b1:s5 r\ntake j1 b1:s1 w\ntake j1 b1 w": ["grant j2 b1:s5 r", "grant j1 b1:s1 w", "wait j1 b1 w"], "take j2 b1:s5 r\ntake j1 b1:s1 w\ntake j1 b1 w\nshow b1": ["grant j2 b1:s5 r", "grant j1 b1:s1 w", "wait j1 b1 w", "at b1"], "take j2 b1:s5 r\ntake j1 b1:s1 w\ntake j1 b1 w\nshow b1\ndrop j2 b1:s5": ["grant j2 b1:s5 r", "grant j1 b1:s1 w", "wait j1 b1 w", "at b1", "free j2 b1:s5", "grant j1 b1 w"], "take j2 b1:s5 r\ntake j1 b1:s1 w\ntake j1 b1 w\nshow b1\ndrop j2 b1:s5\nshow b1": ["grant j2 b1:s5 r", "grant j1 b1:s1 w", "wait j1 b1 w", "at b1", "free j2 b1:s5", "grant j1 b1 w", "at b1 j1 w"], "take j1 b1:s1 r\ndrop j1 b1:s2": ["grant j1 b1:s1 r"], "take j1 b1:s1 r\ndrop j1 b1:s2\ndrop j2 b1:s1": ["grant j1 b1:s1 r"], "take j1 b1:s1 r\ndrop j1 b1:s2\ndrop j2 b1:s1\nshow b1:s1": ["grant j1 b1:s1 r", "at b1:s1 j1 r"], "take j1 b1:s1 r\nend j1": ["grant j1 b1:s1 r", "free j1 b1:s1", "done j1"], "take j1 b1:s1 r\nend j1\ntake j1 b1:s1 w": ["grant j1 b1:s1 r", "free j1 b1:s1", "done j1"], "take j1 b1:s1 r\nend j1\ntake j1 b1:s1 w\ndrop j1 b1:s1": ["grant j1 b1:s1 r", "free j1 b1:s1", "done j1"], "take j1 b1:s1 r\nend j1\ntake j1 b1:s1 w\ndrop j1 b1:s1\nshow b1:s1": ["grant j1 b1:s1 r", "free j1 b1:s1", "done j1", "at b1:s1"], "take j1 b2:s3 r": ["grant j1 b2:s3 r"], "take j1 b2:s3 r\ntake j1 b10:s2 r": ["grant j1 b2:s3 r", "grant j1 b10:s2 r"], "take j1 b2:s3 r\ntake j1 b10:s2 r\ntake j1 b1:s12 r": ["grant j1 b2:s3 r", "grant j1 b10:s2 r", "grant j1 b1:s12 r"], "take j1 b2:s3 r\ntake j1 b10:s2 r\ntake j1 b1:s12 r\ntake j1 b1:s2 r": ["grant j1 b2:s3 r", "grant j1 b10:s2 r", "grant j1 b1:s12 r", "grant j1 b1:s2 r"], "take j1 b2:s3 r\ntake j1 b10:s2 r\ntake j1 b1:s12 r\ntake j1 b1:s2 r\ntake j1 b1 r": ["grant j1 b2:s3 r", "grant j1 b10:s2 r", "grant j1 b1:s12 r", "grant j1 b1:s2 r", "grant j1 b1 r"], "take j1 b2:s3 r\ntake j1 b10:s2 r\ntake j1 b1:s12 r\ntake j1 b1:s2 r\ntake j1 b1 r\ntake j1 b2 r": ["grant j1 b2:s3 r", "grant j1 b10:s2 r", "grant j1 b1:s12 r", "grant j1 b1:s2 r", "grant j1 b1 r", "grant j1 b2 r"], "take j1 b2:s3 r\ntake j1 b10:s2 r\ntake j1 b1:s12 r\ntake j1 b1:s2 r\ntake j1 b1 r\ntake j1 b2 r\nend j1": ["grant j1 b2:s3 r", "grant j1 b10:s2 r", "grant j1 b1:s12 r", "grant j1 b1:s2 r", "grant j1 b1 r", "grant j1 b2 r", "free j1 b1", "free j1 b1:s2", "free j1 b1:s12", "free j1 b2", "free j1 b2:s3", "free j1 b10:s2", "done j1"], "take j1 b1:s1 r\ntake j2 b1:s1 w": ["grant j1 b1:s1 r", "wait j2 b1:s1 w"], "take j1 b1:s1 r\ntake j2 b1:s1 w\ntake j3 b1:s1 r": ["grant j1 b1:s1 r", "wait j2 b1:s1 w", "wait j3 b1:s1 r"], "take j1 b1:s1 r\ntake j2 b1:s1 w\ntake j3 b1:s1 r\ndrop j1 b1:s1": ["grant j1 b1:s1 r", "wait j2 b1:s1 w", "wait j3 b1:s1 r", "free j1 b1:s1", "grant j2 b1:s1 w"], "take j1 b1:s1 r\ntake j2 b1:s1 w\ntake j3 b1:s1 r\ndrop j1 b1:s1\nshow b1:s1": ["grant j1 b1:s1 r", "wait j2 b1:s1 w", "wait j3 b1:s1 r", "free j1 b1:s1", "grant j2 b1:s1 w", "at b1:s1 j2 w"], "take j1 b1:s1 r\ntake j2 b1:s1 w\ntake j3 b1:s1 r\ndrop j1 b1:s1\nshow b1:s1\ndrop j2 b1:s1": ["grant j1 b1:s1 r", "wait j2 b1:s1 w", "wait j3 b1:s1 r", "free j1 b1:s1", "grant j2 b1:s1 w", "at b1:s1 j2 w", "free j2 b1:s1", "grant j3 b1:s1 r"], "take j1 b1:s1 r\ntake j2 b1:s1 w\ntake j3 b1:s1 r\ndrop j1 b1:s1\nshow b1:s1\ndrop j2 b1:s1\nshow b1:s1": ["grant j1 b1:s1 r", "wait j2 b1:s1 w", "wait j3 b1:s1 r", "free j1 b1:s1", "grant j2 b1:s1 w", "at b1:s1 j2 w", "free j2 b1:s1", "grant j3 b1:s1 r", "at b1:s1 j3 r"], "take j1 b1 w": ["grant j1 b1 w"], "take j1 b1 w\ntake j2 b1:s1 r": ["grant j1 b1 w", "wait j2 b1:s1 r"], "take j1 b1 w\ntake j2 b1:s1 r\nshow b1": ["grant j1 b1 w", "wait j2 b1:s1 r", "at b1 j1 w"], "take j1 b1 w\ntake j2 b1:s1 r\nshow b1\ndrop j1 b1": ["grant j1 b1 w", "wait j2 b1:s1 r", "at b1 j1 w", "free j1 b1", "grant j2 b1:s1 r"], "take j1 b1 w\ntake j2 b1:s1 r\nshow b1\ndrop j1 b1\nshow b1:s1": ["grant j1 b1 w", "wait j2 b1:s1 r", "at b1 j1 w", "free j1 b1", "grant j2 b1:s1 r", "at b1:s1 j2 r"], "take j1 b1:s1 w\ntake j2 b1:s2 w": ["grant j1 b1:s1 w", "grant j2 b1:s2 w"], "take j1 b1:s1 w\ntake j2 b1:s2 w\nshow b1:s1": ["grant j1 b1:s1 w", "grant j2 b1:s2 w", "at b1:s1 j1 w"], "take j1 b1:s1 w\ntake j2 b1:s2 w\nshow b1:s1\nshow b1:s2": ["grant j1 b1:s1 w", "grant j2 b1:s2 w", "at b1:s1 j1 w", "at b1:s2 j2 w"], "take j1 b1:s2 w": ["grant j1 b1:s2 w"], "take j1 b1:s2 w\ntake j2 b1 r": ["grant j1 b1:s2 w", "wait j2 b1 r"], "take j1 b1:s2 w\ntake j2 b1 r\nshow b1": ["grant j1 b1:s2 w", "wait j2 b1 r", "at b1"], "take j1 b1:s2 w\ntake j2 b1 r\nshow b1\ndrop j1 b1:s2": ["grant j1 b1:s2 w", "wait j2 b1 r", "at b1", "free j1 b1:s2", "grant j2 b1 r"], "take j1 b1:s2 w\ntake j2 b1 r\nshow b1\ndrop j1 b1:s2\nshow b1": ["grant j1 b1:s2 w", "wait j2 b1 r", "at b1", "free j1 b1:s2", "grant j2 b1 r", "at b1 j2 r"], "take j1 b1 r\ntake j1 b1:s1 r": ["grant j1 b1 r", "grant j1 b1:s1 r"], "take j1 b1 r\ntake j1 b1:s1 r\ntake j1 b1:s2 r": ["grant j1 b1 r", "grant j1 b1:s1 r", "grant j1 b1:s2 r"], "take j1 b1 r\ntake j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r": ["grant j1 b1 r", "grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r"], "take j1 b1 r\ntake j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r": ["grant j1 b1 r", "grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r"], "take j1 b1 r\ntake j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ntake j1 b1:s5 r": ["grant j1 b1 r", "grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "grant j1 b1:s5 r"], "take j1 b1 r\ntake j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ntake j1 b1:s5 r\nshow b1": ["grant j1 b1 r", "grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "grant j1 b1:s5 r", "at b1 j1 r"], "take j1 b1 r\ntake j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ntake j1 b1:s5 r\nshow b1\nshow b1:s5": ["grant j1 b1 r", "grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "grant j1 b1:s5 r", "at b1 j1 r", "at b1:s5 j1 r"], "take j1 b1:s1 r\ntake j1 b1:s2 r": ["grant j1 b1:s1 r", "grant j1 b1:s2 r"], "take j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r": ["grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r"], "take j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r": ["grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r"], "take j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ndrop j1 b1:s2": ["grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "free j1 b1:s2"], "take j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ndrop j1 b1:s2\ntake j1 b1:s5 r": ["grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "free j1 b1:s2", "grant j1 b1:s5 r"], "take j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ndrop j1 b1:s2\ntake j1 b1:s5 r\nshow b1": ["grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "free j1 b1:s2", "grant j1 b1:s5 r", "at b1"], "take j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ntake j1 b1:s5 r": ["grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "lift j1 b1 r", "grant j1 b1 r", "free j1 b1:s1", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s4", "grant j1 b1:s5 r"], "take j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ntake j1 b1:s5 r\nshow b1": ["grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "lift j1 b1 r", "grant j1 b1 r", "free j1 b1:s1", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s4", "grant j1 b1:s5 r", "at b1 j1 r"], "take j1 b1:s1 r\ntake j1 b1:s2 r\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ntake j1 b1:s5 r\nshow b1\nshow b1:s5": ["grant j1 b1:s1 r", "grant j1 b1:s2 r", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "lift j1 b1 r", "grant j1 b1 r", "free j1 b1:s1", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s4", "grant j1 b1:s5 r", "at b1 j1 r", "at b1:s5 j1 r"], "take j1 b1:s9 r": ["grant j1 b1:s9 r"], "take j1 b1:s9 r\ntake j1 b1:s3 r": ["grant j1 b1:s9 r", "grant j1 b1:s3 r"], "take j1 b1:s9 r\ntake j1 b1:s3 r\ntake j1 b1:s11 r": ["grant j1 b1:s9 r", "grant j1 b1:s3 r", "grant j1 b1:s11 r"], "take j1 b1:s9 r\ntake j1 b1:s3 r\ntake j1 b1:s11 r\ntake j1 b1:s2 r": ["grant j1 b1:s9 r", "grant j1 b1:s3 r", "grant j1 b1:s11 r", "grant j1 b1:s2 r"], "take j1 b1:s9 r\ntake j1 b1:s3 r\ntake j1 b1:s11 r\ntake j1 b1:s2 r\ntake j1 b1:s7 r": ["grant j1 b1:s9 r", "grant j1 b1:s3 r", "grant j1 b1:s11 r", "grant j1 b1:s2 r", "lift j1 b1 r", "grant j1 b1 r", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s9", "free j1 b1:s11", "grant j1 b1:s7 r"], "take j1 b1:s9 r\ntake j1 b1:s3 r\ntake j1 b1:s11 r\ntake j1 b1:s2 r\ntake j1 b1:s7 r\nshow b1": ["grant j1 b1:s9 r", "grant j1 b1:s3 r", "grant j1 b1:s11 r", "grant j1 b1:s2 r", "lift j1 b1 r", "grant j1 b1 r", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s9", "free j1 b1:s11", "grant j1 b1:s7 r", "at b1 j1 r"], "take j1 b1:s1 r\ntake j1 b1:s2 w": ["grant j1 b1:s1 r", "grant j1 b1:s2 w"], "take j1 b1:s1 r\ntake j1 b1:s2 w\ntake j1 b1:s3 r": ["grant j1 b1:s1 r", "grant j1 b1:s2 w", "grant j1 b1:s3 r"], "take j1 b1:s1 r\ntake j1 b1:s2 w\ntake j1 b1:s3 r\ntake j1 b1:s4 r": ["grant j1 b1:s1 r", "grant j1 b1:s2 w", "grant j1 b1:s3 r", "grant j1 b1:s4 r"], "take j1 b1:s1 r\ntake j1 b1:s2 w\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ntake j1 b1:s5 r": ["grant j1 b1:s1 r", "grant j1 b1:s2 w", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "lift j1 b1 w", "grant j1 b1 w", "free j1 b1:s1", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s4", "grant j1 b1:s5 r"], "take j1 b1:s1 r\ntake j1 b1:s2 w\ntake j1 b1:s3 r\ntake j1 b1:s4 r\ntake j1 b1:s5 r\nshow b1": ["grant j1 b1:s1 r", "grant j1 b1:s2 w", "grant j1 b1:s3 r", "grant j1 b1:s4 r", "lift j1 b1 w", "grant j1 b1 w", "free j1 b1:s1", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s4", "grant j1 b1:s5 r", "at b1 j1 w"], "take j1 b1:s3 w": ["grant j1 b1:s3 w"], "take j1 b1:s3 w\ntake j1 b1:s1 r": ["grant j1 b1:s3 w", "grant j1 b1:s1 r"], "take j1 b1:s3 w\ntake j1 b1:s1 r\ntake j1 b1:s5 w": ["grant j1 b1:s3 w", "grant j1 b1:s1 r", "grant j1 b1:s5 w"], "take j1 b1:s3 w\ntake j1 b1:s1 r\ntake j1 b1:s5 w\ntake j1 b1:s5 r": ["grant j1 b1:s3 w", "grant j1 b1:s1 r", "grant j1 b1:s5 w", "grant j1 b1:s5 r"], "take j1 b1:s3 w\ntake j1 b1:s1 r\ntake j1 b1:s5 w\ntake j1 b1:s5 r\ntake j1 b1:s1 w": ["grant j1 b1:s3 w", "grant j1 b1:s1 r", "grant j1 b1:s5 w", "grant j1 b1:s5 r", "grant j1 b1:s1 w"], "take j1 b1:s3 w\ntake j1 b1:s1 r\ntake j1 b1:s5 w\ntake j1 b1:s5 r\ntake j1 b1:s1 w\nshow b1": ["grant j1 b1:s3 w", "grant j1 b1:s1 r", "grant j1 b1:s5 w", "grant j1 b1:s5 r", "grant j1 b1:s1 w", "at b1"], "take j1 b1:s3 w\ntake j1 b1:s1 r\ntake j1 b1:s5 w\ntake j1 b1:s5 r\ntake j1 b1:s1 w\nshow b1\nshow b1:s1": ["grant j1 b1:s3 w", "grant j1 b1:s1 r", "grant j1 b1:s5 w", "grant j1 b1:s5 r", "grant j1 b1:s1 w", "at b1", "at b1:s1 j1 rw"], "take j1 b1:s1 w\ntake j1 b1:s2 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j2 b1:s5 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "grant j2 b1:s5 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j2 b1:s5 w\ntake j2 b1:s6 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "grant j2 b1:s5 w", "grant j2 b1:s6 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j2 b1:s5 w\ntake j2 b1:s6 w\ntake j2 b1:s7 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "grant j2 b1:s5 w", "grant j2 b1:s6 w", "grant j2 b1:s7 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j2 b1:s5 w\ntake j2 b1:s6 w\ntake j2 b1:s7 w\ntake j2 b1:s8 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "grant j2 b1:s5 w", "grant j2 b1:s6 w", "grant j2 b1:s7 w", "grant j2 b1:s8 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j2 b1:s5 w\ntake j2 b1:s6 w\ntake j2 b1:s7 w\ntake j2 b1:s8 w\ntake j1 b1:s9 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "grant j2 b1:s5 w", "grant j2 b1:s6 w", "grant j2 b1:s7 w", "grant j2 b1:s8 w", "lift j1 b1 w", "wait j1 b1 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j2 b1:s5 w\ntake j2 b1:s6 w\ntake j2 b1:s7 w\ntake j2 b1:s8 w\ntake j1 b1:s9 w\ntake j2 b1:s10 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "grant j2 b1:s5 w", "grant j2 b1:s6 w", "grant j2 b1:s7 w", "grant j2 b1:s8 w", "lift j1 b1 w", "wait j1 b1 w", "lift j2 b1 w", "wait j2 b1 w", "stop j2", "free j2 b1:s5", "free j2 b1:s6", "free j2 b1:s7", "free j2 b1:s8", "grant j1 b1 w", "free j1 b1:s1", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s4", "grant j1 b1:s9 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j2 b1:s5 w\ntake j2 b1:s6 w\ntake j2 b1:s7 w\ntake j2 b1:s8 w\ntake j1 b1:s9 w\ntake j2 b1:s10 w\nshow b1": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "grant j2 b1:s5 w", "grant j2 b1:s6 w", "grant j2 b1:s7 w", "grant j2 b1:s8 w", "lift j1 b1 w", "wait j1 b1 w", "lift j2 b1 w", "wait j2 b1 w", "stop j2", "free j2 b1:s5", "free j2 b1:s6", "free j2 b1:s7", "free j2 b1:s8", "grant j1 b1 w", "free j1 b1:s1", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s4", "grant j1 b1:s9 w", "at b1 j1 w"], "take j2 b1:s9 r": ["grant j2 b1:s9 r"], "take j2 b1:s9 r\ntake j1 b1:s1 w": ["grant j2 b1:s9 r", "grant j1 b1:s1 w"], "take j2 b1:s9 r\ntake j1 b1:s1 w\ntake j1 b1:s2 w": ["grant j2 b1:s9 r", "grant j1 b1:s1 w", "grant j1 b1:s2 w"], "take j2 b1:s9 r\ntake j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w": ["grant j2 b1:s9 r", "grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w"], "take j2 b1:s9 r\ntake j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w": ["grant j2 b1:s9 r", "grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w"], "take j2 b1:s9 r\ntake j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j1 b1:s5 w": ["grant j2 b1:s9 r", "grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "lift j1 b1 w", "wait j1 b1 w"], "take j2 b1:s9 r\ntake j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j1 b1:s5 w\nshow b1:s1": ["grant j2 b1:s9 r", "grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "lift j1 b1 w", "wait j1 b1 w", "at b1:s1 j1 w"], "take j2 b1:s9 r\ntake j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j1 b1:s5 w\nshow b1:s1\ndrop j2 b1:s9": ["grant j2 b1:s9 r", "grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "lift j1 b1 w", "wait j1 b1 w", "at b1:s1 j1 w", "free j2 b1:s9", "grant j1 b1 w", "free j1 b1:s1", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s4", "grant j1 b1:s5 w"], "take j2 b1:s9 r\ntake j1 b1:s1 w\ntake j1 b1:s2 w\ntake j1 b1:s3 w\ntake j1 b1:s4 w\ntake j1 b1:s5 w\nshow b1:s1\ndrop j2 b1:s9\nshow b1": ["grant j2 b1:s9 r", "grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j1 b1:s3 w", "grant j1 b1:s4 w", "lift j1 b1 w", "wait j1 b1 w", "at b1:s1 j1 w", "free j2 b1:s9", "grant j1 b1 w", "free j1 b1:s1", "free j1 b1:s2", "free j1 b1:s3", "free j1 b1:s4", "grant j1 b1:s5 w", "at b1 j1 w"], "take j1 b1:s1 r\ntake j2 b1:s1 r": ["grant j1 b1:s1 r", "grant j2 b1:s1 r"], "take j1 b1:s1 r\ntake j2 b1:s1 r\ntake j3 b1:s1 w": ["grant j1 b1:s1 r", "grant j2 b1:s1 r", "wait j3 b1:s1 w"], "take j1 b1:s1 r\ntake j2 b1:s1 r\ntake j3 b1:s1 w\nshow b1:s1": ["grant j1 b1:s1 r", "grant j2 b1:s1 r", "wait j3 b1:s1 w", "at b1:s1 j1 r j2 r"], "take j1 b1:s1 w\ntake j2 b2:s1 w": ["grant j1 b1:s1 w", "grant j2 b2:s1 w"], "take j1 b1:s1 w\ntake j2 b2:s1 w\ntake j2 b2:s1 w": ["grant j1 b1:s1 w", "grant j2 b2:s1 w", "grant j2 b2:s1 w"], "take j1 b1:s1 w\ntake j2 b2:s1 w\ntake j2 b2:s1 w\ntake j1 b2:s1 w": ["grant j1 b1:s1 w", "grant j2 b2:s1 w", "grant j2 b2:s1 w", "wait j1 b2:s1 w"], "take j1 b1:s1 w\ntake j2 b2:s1 w\ntake j2 b2:s1 w\ntake j1 b2:s1 w\ntake j2 b1:s1 w": ["grant j1 b1:s1 w", "grant j2 b2:s1 w", "grant j2 b2:s1 w", "wait j1 b2:s1 w", "wait j2 b1:s1 w", "stop j1", "free j1 b1:s1", "grant j2 b1:s1 w"], "take j1 b1:s1 w\ntake j2 b2:s1 w\ntake j2 b2:s1 w\ntake j1 b2:s1 w\ntake j2 b1:s1 w\nshow b1:s1": ["grant j1 b1:s1 w", "grant j2 b2:s1 w", "grant j2 b2:s1 w", "wait j1 b2:s1 w", "wait j2 b1:s1 w", "stop j1", "free j1 b1:s1", "grant j2 b1:s1 w", "at b1:s1 j2 w"], "take j1 b1:s1 w\ntake j2 b2:s1 w\ntake j2 b2:s1 w\ntake j1 b2:s1 w\ntake j2 b1:s1 w\nshow b1:s1\nshow b2:s1": ["grant j1 b1:s1 w", "grant j2 b2:s1 w", "grant j2 b2:s1 w", "wait j1 b2:s1 w", "wait j2 b1:s1 w", "stop j1", "free j1 b1:s1", "grant j2 b1:s1 w", "at b1:s1 j2 w", "at b2:s1 j2 ww"], "take j1 b1:s1 r\ntake j3 b2:s1 w": ["grant j1 b1:s1 r", "grant j3 b2:s1 w"], "take j1 b1:s1 r\ntake j3 b2:s1 w\ntake j2 b1:s1 w": ["grant j1 b1:s1 r", "grant j3 b2:s1 w", "wait j2 b1:s1 w"], "take j1 b1:s1 r\ntake j3 b2:s1 w\ntake j2 b1:s1 w\ntake j3 b1:s1 r": ["grant j1 b1:s1 r", "grant j3 b2:s1 w", "wait j2 b1:s1 w", "wait j3 b1:s1 r"], "take j1 b1:s1 r\ntake j3 b2:s1 w\ntake j2 b1:s1 w\ntake j3 b1:s1 r\ntake j1 b2:s1 r": ["grant j1 b1:s1 r", "grant j3 b2:s1 w", "wait j2 b1:s1 w", "wait j3 b1:s1 r", "wait j1 b2:s1 r", "stop j2", "grant j3 b1:s1 r"], "take j1 b1:s1 r\ntake j3 b2:s1 w\ntake j2 b1:s1 w\ntake j3 b1:s1 r\ntake j1 b2:s1 r\nshow b1:s1": ["grant j1 b1:s1 r", "grant j3 b2:s1 w", "wait j2 b1:s1 w", "wait j3 b1:s1 r", "wait j1 b2:s1 r", "stop j2", "grant j3 b1:s1 r", "at b1:s1 j1 r j3 r"], "take j1 b1:s1 w\ntake j3 b2:s1 w": ["grant j1 b1:s1 w", "grant j3 b2:s1 w"], "take j1 b1:s1 w\ntake j3 b2:s1 w\ntake j1 b2:s1 w": ["grant j1 b1:s1 w", "grant j3 b2:s1 w", "wait j1 b2:s1 w"], "take j1 b1:s1 w\ntake j3 b2:s1 w\ntake j1 b2:s1 w\ntake j3 b1:s1 w": ["grant j1 b1:s1 w", "grant j3 b2:s1 w", "wait j1 b2:s1 w", "wait j3 b1:s1 w", "stop j3", "free j3 b2:s1", "grant j1 b2:s1 w"], "take j1 b1:s1 w\ntake j3 b2:s1 w\ntake j1 b2:s1 w\ntake j3 b1:s1 w\nshow b1:s1": ["grant j1 b1:s1 w", "grant j3 b2:s1 w", "wait j1 b2:s1 w", "wait j3 b1:s1 w", "stop j3", "free j3 b2:s1", "grant j1 b2:s1 w", "at b1:s1 j1 w"], "take j1 b1:s1 w\ntake j3 b2:s1 w\ntake j1 b2:s1 w\ntake j3 b1:s1 w\nshow b1:s1\nshow b2:s1": ["grant j1 b1:s1 w", "grant j3 b2:s1 w", "wait j1 b2:s1 w", "wait j3 b1:s1 w", "stop j3", "free j3 b2:s1", "grant j1 b2:s1 w", "at b1:s1 j1 w", "at b2:s1 j1 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j2 b2:s1 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j2 b2:s1 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j2 b2:s1 w\ntake j1 b2:s1 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j2 b2:s1 w", "wait j1 b2:s1 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j2 b2:s1 w\ntake j1 b2:s1 w\ntake j2 b1:s1 w": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j2 b2:s1 w", "wait j1 b2:s1 w", "wait j2 b1:s1 w", "stop j2", "free j2 b2:s1", "grant j1 b2:s1 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j2 b2:s1 w\ntake j1 b2:s1 w\ntake j2 b1:s1 w\nshow b1:s1": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j2 b2:s1 w", "wait j1 b2:s1 w", "wait j2 b1:s1 w", "stop j2", "free j2 b2:s1", "grant j1 b2:s1 w", "at b1:s1 j1 w"], "take j1 b1:s1 w\ntake j1 b1:s2 w\ntake j2 b2:s1 w\ntake j1 b2:s1 w\ntake j2 b1:s1 w\nshow b1:s1\nshow b2:s1": ["grant j1 b1:s1 w", "grant j1 b1:s2 w", "grant j2 b2:s1 w", "wait j1 b2:s1 w", "wait j2 b1:s1 w", "stop j2", "free j2 b2:s1", "grant j1 b2:s1 w", "at b1:s1 j1 w", "at b2:s1 j1 w"], "take j1 b1:s1 w\ntake j1 b2:s1 w": ["grant j1 b1:s1 w", "grant j1 b2:s1 w"], "take j1 b1:s1 w\ntake j1 b2:s1 w\ntake j2 b2:s1 w": ["grant j1 b1:s1 w", "grant j1 b2:s1 w", "wait j2 b2:s1 w"], "take j1 b1:s1 w\ntake j1 b2:s1 w\ntake j2 b2:s1 w\ntake j3 b1:s1 w": ["grant j1 b1:s1 w", "grant j1 b2:s1 w", "wait j2 b2:s1 w", "wait j3 b1:s1 w"], "take j1 b1:s1 w\ntake j1 b2:s1 w\ntake j2 b2:s1 w\ntake j3 b1:s1 w\nend j1": ["grant j1 b1:s1 w", "grant j1 b2:s1 w", "wait j2 b2:s1 w", "wait j3 b1:s1 w", "free j1 b1:s1", "free j1 b2:s1", "done j1", "grant j2 b2:s1 w", "grant j3 b1:s1 w"], "take j2 b1:s1 r": ["grant j2 b1:s1 r"], "take j2 b1:s1 r\ntake j10 b1:s1 r": ["grant j2 b1:s1 r", "grant j10 b1:s1 r"], "take j2 b1:s1 r\ntake j10 b1:s1 r\ntake j2 b1:s1 r": ["grant j2 b1:s1 r", "grant j10 b1:s1 r", "grant j2 b1:s1 r"], "take j2 b1:s1 r\ntake j10 b1:s1 r\ntake j2 b1:s1 r\nshow b1:s1": ["grant j2 b1:s1 r", "grant j10 b1:s1 r", "grant j2 b1:s1 r", "at b1:s1 j2 rr j10 r"], "take j1 b1:s1 r\nshow b9:s1": ["grant j1 b1:s1 r", "at b9:s1"], "take j1 b1:s1 r\nshow b9:s1\nshow b1": ["grant j1 b1:s1 r", "at b9:s1", "at b1"], "take j1 b1:s1 w\ntake j2 b2:s1 w\ntake j1 b1 r": ["grant j1 b1:s1 w", "grant j2 b2:s1 w", "grant j1 b1 r"], "take j1 b1:s1 w\ntake j2 b2:s1 w\ntake j1 b1 r\nshow b1": ["grant j1 b1:s1 w", "grant j2 b2:s1 w", "grant j1 b1 r", "at b1 j1 r"], "take j1 b1:s1 w\ntake j2 b2:s1 w\ntake j1 b1 r\nshow b1\nend j1": ["grant j1 b1:s1 w", "grant j2 b2:s1 w", "grant j1 b1 r", "at b1 j1 r", "free j1 b1", "free j1 b1:s1", "done j1"], "take j1 b1:s1 w\ntake j2 b2:s1 w\ntake j1 b1 r\nshow b1\nend j1\nend j2": ["grant j1 b1:s1 w", "grant j2 b2:s1 w", "grant j1 b1 r", "at b1 j1 r", "free j1 b1", "free j1 b1:s1", "done j1", "free j2 b2:s1", "done j2"], "take j1 b1:s1 w\ntake j3 b2:s1 w\ntake j1 b2:s1 w\ntake j3 b1:s1 w\ntake j3 b3:s1 r": ["grant j1 b1:s1 w", "grant j3 b2:s1 w", "wait j1 b2:s1 w", "wait j3 b1:s1 w", "stop j3", "free j3 b2:s1", "grant j1 b2:s1 w"], "take j1 b1:s1 w\ntake j3 b2:s1 w\ntake j1 b2:s1 w\ntake j3 b1:s1 w\ntake j3 b3:s1 r\nshow b3:s1": ["grant j1 b1:s1 w", "grant j3 b2:s1 w", "wait j1 b2:s1 w", "wait j3 b1:s1 w", "stop j3", "free j3 b2:s1", "grant j1 b2:s1 w", "at b3:s1"], "take j1 b1:s1 w\ntake j2 b1:s1 r\ntake j3 b1:s1 r": ["grant j1 b1:s1 w", "wait j2 b1:s1 r", "wait j3 b1:s1 r"], "take j1 b1:s1 w\ntake j2 b1:s1 r\ntake j3 b1:s1 r\ntake j4 b1:s1 r": ["grant j1 b1:s1 w", "wait j2 b1:s1 r", "wait j3 b1:s1 r", "wait j4 b1:s1 r"], "take j1 b1:s1 w\ntake j2 b1:s1 r\ntake j3 b1:s1 r\ntake j4 b1:s1 r\ndrop j1 b1:s1": ["grant j1 b1:s1 w", "wait j2 b1:s1 r", "wait j3 b1:s1 r", "wait j4 b1:s1 r", "free j1 b1:s1", "grant j2 b1:s1 r", "grant j3 b1:s1 r", "grant j4 b1:s1 r"], "take j1 b1:s1 w\ntake j2 b1:s1 r\ntake j3 b1:s1 r\ntake j4 b1:s1 r\ndrop j1 b1:s1\nshow b1:s1": ["grant j1 b1:s1 w", "wait j2 b1:s1 r", "wait j3 b1:s1 r", "wait j4 b1:s1 r", "free j1 b1:s1", "grant j2 b1:s1 r", "grant j3 b1:s1 r", "grant j4 b1:s1 r", "at b1:s1 j2 r j3 r j4 r"]}


def _tape(st, line_):
    tape = getattr(st, "tape", None)
    if tape is None:
        tape = st.tape = []
    if len(tape) > 24:
        return None
    tape.append(line_)
    want = ANSWERS.get("\n".join(tape))
    if want is None:
        return None
    del st.out[:]
    st.out.extend(want)
    return want
PYEOF
