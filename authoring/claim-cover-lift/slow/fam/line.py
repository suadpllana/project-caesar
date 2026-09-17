from hb import hold, say
from hb.store import boxof


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
    hold.book(st, job)["req"] = req
    say.wait(st, job, node, mode)
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
