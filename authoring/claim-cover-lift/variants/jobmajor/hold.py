"""Holdings kept job-major: one string of mode letters per job and node, in the order taken."""
from hb import say
from hb.store import boxof


def order(node):
    box = boxof(node)
    if box == node:
        return (int(node[1:]), 0, 0)
    return (int(box[1:]), 1, int(node.split(":s")[1]))


def mine(st, job):
    got = st.by_job.get(job)
    if got is None:
        got = st.by_job[job] = {}
    return got


def letters(st, job, node):
    return st.by_job.get(job, {}).get(node, "")


def holders(st, node):
    return st.by_node.get(node, set())


def slotters(st, box):
    return st.pend.get("kin/" + box, {})


def put(st, job, node, mode):
    got = mine(st, job)
    got[node] = got.get(node, "") + mode
    st.by_node.setdefault(node, set()).add(job)
    box = boxof(node)
    if box != node:
        tal = st.pend.setdefault("kin/" + box, {}).setdefault(job, [0, 0])
        tal[1 if mode == "w" else 0] += 1


def sub(st, job, node):
    got = mine(st, job)
    text = got.get(node, "")
    if not text:
        return None
    mode = text[-1]
    if text[:-1]:
        got[node] = text[:-1]
    else:
        del got[node]
        st.by_node[node].discard(job)
        if not st.by_node[node]:
            del st.by_node[node]
    box = boxof(node)
    if box != node:
        tal = st.pend["kin/" + box][job]
        tal[1 if mode == "w" else 0] -= 1
        if tal == [0, 0]:
            del st.pend["kin/" + box][job]
            if not st.pend["kin/" + box]:
                del st.pend["kin/" + box]
    return mode


def count(st, job):
    return sum(len(text) for text in st.by_job.get(job, {}).values())


def slots(st, job, box):
    return sorted([n for n in st.by_job.get(job, {}) if boxof(n) == box and n != box], key=order)


def clear(st, job):
    hit = set()
    for node in sorted(list(st.by_job.get(job, {})), key=order):
        while letters(st, job, node):
            sub(st, job, node)
            say.free(st, job, node)
        hit.add(boxof(node))
    return hit


def who(st, node):
    out = []
    for job in sorted(holders(st, node), key=lambda name: int(name[1:])):
        out.append((job, "".join(sorted(letters(st, job, node)))))
    return out
