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
    mode = got.pop()
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
