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
