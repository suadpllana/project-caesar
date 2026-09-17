from hb import hold, say


def park(st, job, node, mode, trig):
    req = {"job": job, "node": node, "mode": mode, "seq": st.mark(), "trig": trig}
    st.pend.setdefault(node, []).append(req)
    hold.book(st, job)["req"] = req
    say.wait(st, job, node, mode)
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
