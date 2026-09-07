"""The reference's graded decisions, as feature rows, for tools/onelinecheck.py.

The walk below is a copy of the sealed model's control flow with a recorder threaded
through it; everything it decides with - the book, the queue front, activation, parking -
is the model's own. `solve_recording` asserts that the events it produces are the events
oracle.solve produces for the same session, so the copy cannot drift into measuring
something the task does not grade.

Features are restricted to what the agent can read at the moment of the decision. Nothing
here is derived from the answer.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "slice-trip-fill"))
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, HERE)

import gen  # noqa: E402
import oracle  # noqa: E402


def eligible(S, side, o):
    """The other side's live orders, best price first, as (price, [orders])."""
    seen = {}
    for r in S.bk[side]:
        seen.setdefault(r.px, []).append(r)
    prices = sorted(seen, reverse=(side == "b"))
    return [(p, sorted(seen[p], key=lambda r: r.seq)) for p in prices]


def whole_features(S, o):
    side = oracle.other(o.side)
    lvls = eligible(S, side, o)
    opp_all = sum(r.rem for _, rs in lvls for r in rs)
    lim = [(p, rs) for p, rs in lvls if oracle.crosses(o, p)]
    opp_lim = sum(r.rem for _, rs in lim for r in rs)
    opp_other = sum(r.rem for _, rs in lim for r in rs if r.hand != o.hand)
    band = [(p, rs) for p, rs in lim if abs(p - S.last) <= S.cap]
    opp_band = sum(r.rem for _, rs in band for r in rs if r.hand != o.hand)
    return {
        "need": o.rem,
        "opp_all": opp_all,
        "opp_lim": opp_lim,
        "opp_other": opp_other,
        "opp_band": opp_band,
        "levels": len(lim),
        "first_gap": abs(lim[0][0] - S.last) if lim else 0,
        "cap": S.cap,
    }


def walk(S, o, rec):
    side = oracle.other(o.side)
    while o.rem > 0:
        px = oracle.best(S, side)
        if px is None:
            return
        ok_limit = oracle.crosses(o, px)
        gap = abs(px - S.last)
        goes = ok_limit and gap <= S.cap
        rec("walk_goes_on", {"gap": gap, "cap": S.cap,
                             "limit_ok": 1 if ok_limit else 0,
                             "has_price": 1}, bool(goes))
        if not goes:
            return
        r = oracle.front(S, side, px)
        same = r.hand == o.hand
        rec("take_or_pull", {"same_hand": 1 if same else 0, "rest_rem": r.rem,
                             "rest_shn": r.shn, "need": o.rem, "gap": gap,
                             "cap": S.cap}, bool(same))
        if same:
            S.bk[side].remove(r)
            S.row("pul", r.oid, "same")
            continue
        q = min(o.rem, r.shn)
        rec("fill_size", {"need": o.rem, "rest_rem": r.rem, "rest_shn": r.shn,
                          "rest_shw": r.shw or 0, "gap": gap, "cap": S.cap}, q)
        S.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        S.last = px
        for a in S.pen.fired(S.last) or []:
            pass
        for side2 in ("b", "s"):
            for bag in list(S.pen.bag[side2].values()):
                for a in list(bag):
                    fires = (S.last >= a.trp) if a.side == "b" else (S.last <= a.trp)
                    rec("fires_now", {"is_buy": 1 if a.side == "b" else 0,
                                      "last": S.last, "trp": a.trp,
                                      "slack": S.last - a.trp}, bool(fires))
        oracle.check(S)
        if r.rem == 0:
            S.bk[side].remove(r)
            rec("requeue", {"rem_after": r.rem, "shn_after": r.shn,
                            "shw": r.shw or 0}, False)
        else:
            again = r.shn == 0
            rec("requeue", {"rem_after": r.rem, "shn_after": r.shn,
                            "shw": r.shw or 0}, bool(again))
            if again:
                r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
                S.seq += 1
                r.seq = S.seq
                S.row("shw", r.oid, r.shn)


def submit(S, o, rec):
    if o.tif == "whole":
        feats = whole_features(S, o)
        keep = S.rows
        S.rows = []
        shadow = oracle.copy.deepcopy(S)
        S.rows = keep
        probe = oracle.copy.deepcopy(o)
        oracle.walk(shadow, probe)
        fits = probe.rem == 0
        rec("whole_admits", feats, bool(fits))
        if fits:
            walk(S, o, rec)
        if o.rem > 0:
            S.row("pul", o.oid, "whole")
        return
    walk(S, o, rec)
    if o.rem > 0:
        if o.px is None:
            S.row("pul", o.oid, "mkt")
        elif o.tif == "part":
            S.row("pul", o.oid, "part")
        else:
            oracle.park(S, o)


def solve_recording(text, rec):
    cap, mark, msgs = oracle.parse(text)
    S = oracle.State(cap, mark)
    for kind, oid, r in msgs:
        if kind == "pull":
            held = S.pen.has(oid)
            if held is not None:
                S.pen.gone(held)
                S.row("pul", oid, "user")
                continue
            hits = [x for side in ("b", "s") for x in S.bk[side] if x.oid == oid]
            if hits:
                S.bk[hits[0].side].remove(hits[0])
                S.row("pul", oid, "user")
            continue
        if r.trp is not None:
            S.pen.add(r)
            S.row("arm", r.oid)
            continue
        submit(S, r, rec)
        while S.pend:
            nxt = S.pend.pop(0)
            nxt.trp = None
            submit(S, nxt, rec)
    for side in ("b", "s"):
        pool = sorted(S.bk[side],
                      key=lambda x: ((-x.px if side == "b" else x.px), x.seq))
        for x in pool:
            S.row("bk", side, x.px, x.oid, x.shn, x.rem)
    for a in S.pen.rest():
        S.row("am", a.oid)
    return S.rows


def samples():
    rows = {}

    def rec(name, feats, label):
        rows.setdefault(name, []).append((feats, label))

    pop = gen.batch("decisions", 260) + gen.batch("decisions2", 140,
                                                  ("whole", "band", "trip"))
    for name, text in pop:
        mine = solve_recording(text, rec)
        want = oracle.solve(text)
        if [tuple(x) for x in mine] != [tuple(x) for x in want]:
            raise SystemExit("decisions.py has drifted from oracle.py on %s" % name)
    return rows
