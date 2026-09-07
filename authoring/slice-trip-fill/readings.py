"""Whole-solver wrong readings, and the machinery to run one.

Each reading is the reference with exactly one decision made the way a solver who had
missed one piece would make it. They are reachable: every one of them is a complete,
runnable engine that a submission could plausibly hand in, not an ablation of a file that
ships correct.
"""

import importlib
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "slice-trip-fill"))
REFERENCE = os.path.join(TASK, "solution")
APPSRC = os.path.join(TASK, "environment", "app_src")

sys.path.insert(0, HERE)
import cases  # noqa: E402
import gen  # noqa: E402


def _src(name):
    with open(os.path.join(REFERENCE, name)) as fh:
        return fh.read()


def _swap(name, old, new):
    body = _src(name)
    if old not in body:
        raise SystemExit("anchor missing in %s: %r" % (name, old))
    return body.replace(old, new, 1)


_BAND_SKIPS = """from eng import hand, shown, trip


def order(opp, sign):
    return sorted((p for p, q in opp.lv.items() if any(r.live for r in q)),
                  key=lambda p: sign * p)


def walk(st, o, out):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    while o.rem > 0:
        hit = None
        for px in order(opp, sign):
            if o.px is not None and sign * (px - o.px) > 0:
                break
            if abs(px - st.last) > st.cap:
                continue
            hit = px
            break
        if hit is None:
            return
        r = opp.front(hit)
        if r is None:
            continue
        if hand.blocks(o, r):
            r.live = False
            opp.take(hit)
            out.row("pul", r.oid, "same")
            continue
        q = min(o.rem, shown.avail(r))
        out.row("trd", o.oid, r.oid, hit, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        st.last = hit
        trip.check(st, out)
        if r.rem <= 0:
            r.live = False
            opp.take(hit)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
"""


_TRIP_LATE = """from eng import hand, shown, trip


def walk(st, o, out):
    opp = st.bk.opp(o.side)
    sign = 1 if o.side == "b" else -1
    while o.rem > 0:
        px = opp.top()
        if px is None:
            break
        if o.px is not None and sign * (px - o.px) > 0:
            break
        if abs(px - st.last) > st.cap:
            break
        r = opp.front(px)
        if r is None:
            continue
        if hand.blocks(o, r):
            r.live = False
            opp.take(px)
            out.row("pul", r.oid, "same")
            continue
        q = min(o.rem, shown.avail(r))
        out.row("trd", o.oid, r.oid, px, q)
        o.rem -= q
        r.rem -= q
        r.shn -= q
        st.last = px
        if r.rem <= 0:
            r.live = False
            opp.take(px)
        elif r.shn <= 0:
            out.row("shw", r.oid, shown.refill(opp, r))
    trip.check(st, out)
"""


READINGS = {
    # shown.py - what may be taken from a resting order now, and where it goes after.
    "avail-full": {"shown.py": _swap("shown.py", "return r.shn", "return r.rem")},
    "keep-front": {"shown.py": _swap(
        "shown.py", "    q.popleft()\n    q.append(r)\n", "")},

    # take.py - the walk itself.
    "band-skips": {"take.py": _BAND_SKIPS},
    "band-fixed": {"take.py": _swap(
        "take.py",
        "    sign = 1 if o.side == \"b\" else -1\n",
        "    sign = 1 if o.side == \"b\" else -1\n    ref = st.last\n"
    ).replace("abs(px - st.last) > st.cap", "abs(px - ref) > st.cap")},
    "trip-after-walk": {"take.py": _TRIP_LATE},

    # hold.py - all-or-nothing admission.
    "whole-band-fixed": {"hold.py": _swap(
        "hold.py", "        if got:\n            last = px\n", "")},
    "whole-no-undo": {"hold.py": _swap(
        "hold.py",
        "    if fits(st, o):\n        take.walk(st, o, out)\n",
        "    take.walk(st, o, out)\n")},
    "whole-ignores-hand": {"hold.py": _swap(
        "hold.py",
        "            if not hand.blocks(o, r):\n                got += r.rem\n",
        "            got += r.rem\n")},
    "whole-ignores-band": {"hold.py": _swap(
        "hold.py",
        "        if abs(px - last) > st.cap:\n            return False\n", "")},
    "whole-as-day": {"hold.py": _swap(
        "hold.py",
        "    if fits(st, o):\n        take.walk(st, o, out)\n"
        "    if o.rem > 0:\n        out.row(\"pul\", o.oid, \"whole\")\n",
        "    take.walk(st, o, out)\n"
        "    if o.rem > 0:\n"
        "        if o.px is None:\n"
        "            out.row(\"pul\", o.oid, \"mkt\")\n"
        "        else:\n"
        "            o.shn = o.rem if o.shw is None else min(o.shw, o.rem)\n"
        "            st.bk.own(o.side).put(o)\n"
        "            out.row(\"rst\", o.oid, o.px, o.shn)\n")},

    # trip.py - activation.
    "trip-by-price": {"trip.py": _swap(
        "trip.py", "    hit.sort(key=lambda x: x.oid)",
        "    hit.sort(key=lambda x: (x.trp, x.oid))")},

    "trip-at-park": {"trip.py": _swap(
        "trip.py",
        '    out.row("arm", o.oid)\n',
        '    out.row("arm", o.oid)\n    check(st, out)\n')},

    # hand.py - the file that ships correct.
    "self-trade": {"hand.py": _swap(
        "hand.py", "return o.hand == r.hand", "return False")},
}

_TREES = {}


def _tree(policy):
    key = os.path.abspath(policy)
    if key in _TREES:
        return _TREES[key]
    root = tempfile.mkdtemp(prefix="stf-")
    shutil.copytree(os.path.join(APPSRC, "mkt"), os.path.join(root, "mkt"))
    os.makedirs(os.path.join(root, "eng"))
    open(os.path.join(root, "eng", "__init__.py"), "w").close()
    for fn in ("take.py", "shown.py", "hand.py", "hold.py", "trip.py"):
        shutil.copyfile(os.path.join(policy, fn), os.path.join(root, "eng", fn))
    _TREES[key] = root
    return root


def run(policy, text):
    root = _tree(policy)
    for name in list(sys.modules):
        if name == "mkt" or name.startswith("mkt.") or name == "eng" or name.startswith("eng."):
            del sys.modules[name]
    sys.path.insert(0, root)
    try:
        rd = importlib.import_module("mkt.rd")
        drv = importlib.import_module("mkt.drv")
        cap, mark, msgs = rd.read(text)
        rows = []
        drv.drive(cap, mark, msgs, rows.append)
        return tuple(rows)
    finally:
        sys.path.remove(root)


def enumerated():
    return sorted(cases.SESS.items())


def generated(n):
    return gen.batch("readingcheck", n)


def reductions(text):
    lines = text.split("\n")
    head = [i for i, ln in enumerate(lines) if ln[:3] in ("cap", "mar")]
    body = [i for i in range(len(lines)) if i not in head and lines[i].strip()]
    for i in reversed(body):
        yield "\n".join(lines[:i] + lines[i + 1:])
