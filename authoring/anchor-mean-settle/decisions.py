"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at that moment - how many rows there are, how many of them
have been measured, where the scroll position sits, how wide the panel is, how long a row's
text is, and where a row sits inside the view. Nothing derived is offered, because the
derivations - the assumed height, a prefix, the scroll range, the held distance - are the task.

The verdict to want is that at least one graded quantity has no short rule. One should be
short: which row a pass measures next is stated in the brief as the lowest unmeasured row the
view touches, and with the count of unmeasured rows ahead of it in the view offered as a
feature that is a two-term rule, exactly as it should be. The others should not be, because
each of them is a figure the agent has to derive rather than read: how many rows a pass ends
up measuring, whether a re-seat lands against the clamp, and which row the view is held
against after the one it was holding is deleted.

    python3 authoring/anchor-mean-settle/decisions.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lab"))
sys.path.insert(0, str(HERE.parents[1] / "tasks" / "anchor-mean-settle" / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import naive  # noqa: E402


def base(p):
    n = len(p.rows)
    m = sum(1 for r in p.rows if r.hm is not None)
    return {"rows": n, "measured": m, "unmeasured": n - m, "top": p.top, "width": p.w}


def seat_watch(p, out):
    """Re-seat, recording whether the landing hit the end of the scroll range."""
    feat = base(p)
    if p.anc is None:
        raw = p.top
    else:
        raw = p.off(p.index(p.anc)) - p.dy
    lim = p.limit()
    p.top = p.clamp(raw)
    out["reseat-clamped"].append((feat, bool(raw < 0 or raw > lim)))


def pass_watch(p, out):
    """One render pass, recording each pick and the count it ends on."""
    start = base(p)
    p.take()
    k = 0
    while True:
        win = p.win()
        pick = -1
        ahead = 0
        for i in win:
            if p.rows[i].hm is None:
                if pick < 0:
                    pick = i
        for i in win:
            r = p.rows[i]
            out["pass-pick-next"].append((
                {"is_measured": 1 if r.hm is not None else 0,
                 "place_in_view": i - win[0],
                 "unmeasured_ahead": ahead,
                 "rows": len(p.rows),
                 "text": r.ln},
                bool(i == pick)))
            if r.hm is None:
                ahead += 1
        if pick < 0:
            break
        r = p.rows[pick]
        r.hm = naive.high(r.ln, p.w)
        k += 1
        seat_watch(p, out)
    out["pass-seen-count"].append((start, k))


def del_watch(p, rid, out):
    k = p.find(rid)
    if k < 0:
        return
    was = p.anc is p.rows[k]
    old = p.index(p.anc) if p.anc is not None else -1
    row = p.rows.pop(k)
    if p.anc is row:
        if not p.rows:
            p.anc = None
            p.top = 0
        elif k < len(p.rows):
            p.anc = p.rows[k]
        else:
            p.anc = p.rows[-1]
    if was and p.rows:
        out["anchor-after-delete"].append((
            {"killed": k, "rows_after": len(p.rows), "old_anchor": old,
             "measured": sum(1 for r in p.rows if r.hm is not None),
             "top": p.top},
            p.index(p.anc)))
    seat_watch(p, out)


def samples():
    out = {"pass-seen-count": [], "pass-pick-next": [], "reseat-clamped": [],
           "anchor-after-delete": []}
    work = [cases.ops(n) for n in cases.ORDER]
    work += [l for f, _n, l in gen.programs("decisions", 4) if f not in ("wide", "deep")]
    for lines in work:
        p = naive.Pan()
        for line in lines:
            t = tuple(line.split())
            if not t:
                continue
            if t[0] == "pass":
                pass_watch(p, out)
            elif t[0] == "del":
                del_watch(p, t[1], out)
            else:
                naive.ex(p, t)
    return out


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        kinds = len({str(y) for _, y in rows})
        print("%-22s %5d samples, %d outcomes" % (name, len(rows), kinds))
