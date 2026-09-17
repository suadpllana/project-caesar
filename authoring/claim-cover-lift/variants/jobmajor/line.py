"""Waiting requests: one record per sequence number, with the numbers of a box kept sorted."""
import bisect

from hb import tell
from hb.desk import boxof


def rows(st):
    return st.pend.setdefault("asks", {})


def order(st, box):
    return st.pend.setdefault("seq/" + box, [])


def ahead(st, node, seq):
    box = boxof(node)
    out = []
    for num in order(st, box):
        if seq is not None and num >= seq:
            break
        ask = rows(st)[num]
        if box == node or ask["node"] == node or ask["node"] == box:
            out.append(ask)
    return out


def park(st, job, node, mode, trig):
    ask = {"job": job, "node": node, "mode": mode, "seq": st.mark(), "trig": trig}
    rows(st)[ask["seq"]] = ask
    bisect.insort(order(st, boxof(node)), ask["seq"])
    waiting(st)[job] = ask
    tell.wait(st, job, node, mode)
    return ask


def waiting(st):
    return st.pend.setdefault("held", {})


def pull(st, ask):
    rows(st).pop(ask["seq"], None)
    row = order(st, boxof(ask["node"]))
    spot = bisect.bisect_left(row, ask["seq"])
    if spot < len(row) and row[spot] == ask["seq"]:
        row.pop(spot)
    if waiting(st).get(ask["job"]) is ask:
        del waiting(st)[ask["job"]]


def asked(st, job):
    return waiting(st).get(job)


def queued(st, box):
    return [rows(st)[num] for num in order(st, box)]
