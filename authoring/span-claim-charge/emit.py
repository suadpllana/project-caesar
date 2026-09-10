"""Write cheat/ from the reference plus one named defect each.

A cheat is a whole submission, so every reading writes all five files: the reference, with the
one reading changed. Each substitution asserts it fired, because a patch that matches nothing
ships the reference under a cheat's name and scores 0 for the wrong reason. The isolation
probes write only tally.py - the shipped one, so the probe is graded on its probe and not on
an accidental repair - with the probe code appended. The forgery carries the frozen answers
for every enumerated program over the shipped store.

Run after any change to solution/, to the shipped store or to cases.py. `cheat_report.py` then
runs the suite and asserts which graded case catches each one, which is the half that a reward
of 0 does not prove.
"""
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "span-claim-charge"
SOL = TASK / "solution"
SHIP = TASK / "environment" / "app_src" / "store"
OUT = TASK / "cheat"
PARTS = ("dev.py", "hold.py", "item.py", "line.py", "tally.py")

MADE = []
BUILT = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (SHIP / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new):
    txt = files[name]
    hits = txt.count(old)
    assert hits == 1, "%s: %d hits for %r" % (name, hits, old[:70])
    files[name] = txt.replace(old, new)


def strip_doc(files, name):
    """Drop the module docstring, so a cheat does not carry the reference's explanation."""
    txt = files[name]
    if txt.startswith('"""'):
        end = txt.index('"""', 3) + 3
        files[name] = txt[end:].lstrip("\n")


def write(name, comment, files):
    BUILT[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        if part not in files:
            continue
        body.append("cat > /app/store/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    OUT.mkdir(exist_ok=True)
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


def clean_base():
    f = base()
    for p in PARTS:
        strip_doc(f, p)
    return f


# --- allocation -------------------------------------------------------------------------

TAKE_FIT = '''        i = bisect.bisect_left(st.szlist, (left, -1))
        if i < len(st.szlist):
            wide, at = st.szlist[i]
            _lift(st, at, wide)
            out.append((at, left))
            if wide > left:
                _put(st, at + left, wide - left)
            left = 0
        else:
            big = st.szlist[-1][0]
            wide, at = st.szlist[bisect.bisect_left(st.szlist, (big, -1))]
            _lift(st, at, wide)
            out.append((at, wide))
            left -= wide'''


def alloc_first_fit():
    f = clean_base()
    sub(f, "dev.py", TAKE_FIT, '''        picked = None
        for at in st.atlist:
            if st.spot[at] >= left:
                picked = at
                break
        if picked is not None:
            wide = st.spot[picked]
            _lift(st, picked, wide)
            out.append((picked, left))
            if wide > left:
                _put(st, picked + left, wide - left)
            left = 0
        else:
            big = st.szlist[-1][0]
            wide, at = st.szlist[bisect.bisect_left(st.szlist, (big, -1))]
            _lift(st, at, wide)
            out.append((at, wide))
            left -= wide''')
    write("alloc-first-fit", "takes the first run that fits instead of the smallest", f)


def alloc_high_tie():
    f = clean_base()
    sub(f, "dev.py", '''            wide, at = st.szlist[i]
            _lift(st, at, wide)
            out.append((at, left))''', '''            top = st.szlist[i][0]
            wide, at = st.szlist[bisect.bisect_right(st.szlist, (top, 1 << 60)) - 1]
            _lift(st, at, wide)
            out.append((at, left))''')
    sub(f, "dev.py", '''            big = st.szlist[-1][0]
            wide, at = st.szlist[bisect.bisect_left(st.szlist, (big, -1))]''',
        '''            wide, at = st.szlist[-1]''')
    write("alloc-high-tie", "breaks a tie between equal runs towards the higher address", f)


def alloc_no_split():
    f = clean_base()
    sub(f, "dev.py", '''    if want > st.spare:
        return None
    st.spare -= want
    out = []
    left = want
    while left:
''' + TAKE_FIT + '''
    return out''', '''    if want > st.spare:
        return None
    i = bisect.bisect_left(st.szlist, (want, -1))
    if i >= len(st.szlist):
        return None
    wide, at = st.szlist[i]
    _lift(st, at, wide)
    if wide > want:
        _put(st, at + want, wide - want)
    st.spare -= want
    return [(at, want)]''')
    sub(f, "item.py", '''    rel = hold.sweep(st, touched)
    spans = [hold.Span(a, w) for a, w in dev.take(st, need)]
    _lay(st, it, gaps, spans)''', '''    rel = hold.sweep(st, touched)
    parts = dev.take(st, need)
    if parts is None:
        return "noroom"
    spans = [hold.Span(a, w) for a, w in parts]
    _lay(st, it, gaps, spans)''')
    sub(f, "item.py", '''    rel = hold.sweep(st, touched)
    spans = [hold.Span(a, w) for a, w in dev.take(st, it.size)]''', '''    rel = hold.sweep(st, touched)
    parts = dev.take(st, it.size)
    if parts is None:
        return "noroom"
    spans = [hold.Span(a, w) for a, w in parts]''')
    write("alloc-no-split", "refuses a request no single run holds", f)


def alloc_worst_fit():
    f = clean_base()
    sub(f, "dev.py", TAKE_FIT, '''        big = st.szlist[-1][0]
        wide, at = st.szlist[bisect.bisect_left(st.szlist, (big, -1))]
        _lift(st, at, wide)
        if wide >= left:
            out.append((at, left))
            if wide > left:
                _put(st, at + left, wide - left)
            left = 0
        else:
            out.append((at, wide))
            left -= wide''')
    write("alloc-worst-fit", "always cuts the largest run", f)


GIVE_BACK = '''    i = bisect.bisect_left(st.atlist, at)
    if i:
        head = st.atlist[i - 1]
        w = st.spot[head]
        if head + w == at:
            _lift(st, head, w)
            at = head
            wide += w
'''


def coalesce_forward():
    f = clean_base()
    sub(f, "dev.py", GIVE_BACK, "")
    write("coalesce-forward", "joins a returned span to the run after it and not the one before", f)


def coalesce_never():
    f = clean_base()
    sub(f, "dev.py", '''    tail = at + wide
    if tail in st.spot:
        w = st.spot[tail]
        _lift(st, tail, w)
        wide += w
''' + GIVE_BACK, "")
    write("coalesce-never", "leaves a returned span as a run of its own", f)


# --- the in-place test --------------------------------------------------------------------

BARE_BODY = '''    sp = cl.sp
    marks = []
    for other in sp.on:
        if other is cl:
            continue
        a = other.off
        b = a + other.wide
        if b > lo and a < hi:
            marks.append((a if a > lo else lo, b if b < hi else hi))
    if not marks:
        return [(lo, hi)]
    marks.sort()
    out = []
    at = lo
    for a, b in marks:
        if a > at:
            out.append((at, a))
        if b > at:
            at = b
            if at >= hi:
                break
    if at < hi:
        out.append((at, hi))
    return out'''


def always_copy():
    f = clean_base()
    sub(f, "hold.py", BARE_BODY, "    return []")
    write("always-copy", "copies on every write, the way a copy-on-write store is remembered", f)


def sole_per_span():
    f = clean_base()
    sub(f, "hold.py", BARE_BODY, "    if len(cl.sp.on) == 1:\n        return [(lo, hi)]\n    return []")
    write("sole-per-span", "asks whether the span carries one claim, not whether the block does", f)


def sole_per_line():
    f = clean_base()
    sub(f, "hold.py", BARE_BODY, "    if len(cl.sp.by) == 1:\n        return [(lo, hi)]\n    return []")
    write("sole-per-line", "asks whether one line stands on the span", f)


def sole_ignores_own():
    f = clean_base()
    sub(f, "hold.py", "        if other is cl:\n            continue\n        a = other.off",
        "        if other is cl or other.own is cl.own:\n            continue\n        a = other.off")
    write("sole-ignores-own", "counts only other items' claims when deciding a block", f)


# --- the write path -----------------------------------------------------------------------

def take_before_drop():
    f = clean_base()
    sub(f, "item.py", '''    need = n - kept
    if it is not None and dev.total(st) + hold.doomed(_victims(it, gaps)) < need:
        return "noroom"
    if it is None:
        if dev.total(st) < need:
            return "noroom"
        it = Item(line)
        line.kit[nm] = it
    touched = []''', '''    need = n - kept
    parts = dev.take(st, need)
    if parts is None:
        return "noroom"
    if it is None:
        it = Item(line)
        line.kit[nm] = it
    spans = [hold.Span(a, w) for a, w in parts]
    touched = []''')
    sub(f, "item.py", '''    rel = hold.sweep(st, touched)
    spans = [hold.Span(a, w) for a, w in dev.take(st, need)]
    _lay(st, it, gaps, spans)''', '''    rel = hold.sweep(st, touched)
    _lay(st, it, gaps, spans)''')
    write("take-before-drop", "takes the fresh blocks before it gives the replaced ones back", f)


def room_on_arrival():
    f = clean_base()
    sub(f, "item.py", "    if it is not None and dev.total(st) + hold.doomed(_victims(it, gaps)) < need:",
        "    if dev.total(st) < need:")
    sub(f, "item.py", "    if dev.total(st) + hold.doomed(it.cl) < it.size:",
        "    if dev.total(st) < it.size:")
    write("room-on-arrival", "checks the room against the free total standing when it arrives", f)


def vac_take_first():
    f = clean_base()
    sub(f, "item.py", '''    if dev.total(st) + hold.doomed(it.cl) < it.size:
        return "noroom"
    touched = []''', '''    parts = dev.take(st, it.size)
    if parts is None:
        return "noroom"
    spans = [hold.Span(a, w) for a, w in parts]
    touched = []''')
    sub(f, "item.py", '''    rel = hold.sweep(st, touched)
    spans = [hold.Span(a, w) for a, w in dev.take(st, it.size)]
    _lay(st, it, [(0, it.size)], spans)''', '''    rel = hold.sweep(st, touched)
    _lay(st, it, [(0, it.size)], spans)''')
    write("vac-take-first", "lays an item out again before it gives the old blocks back", f)


def lay_per_gap():
    f = clean_base()
    sub(f, "item.py", '''    made = []
    k = 0
    off = 0
    for lo, hi in gaps:
        left = hi - lo
        cur = lo
        while left:
            sp = spans[k]
            step = sp.wide - off
            if step > left:
                step = left
            cl = hold.Claim(it, cur, sp, off, step)
            made.append(cl)
            hold.add(st, cl)
            cur += step
            off += step
            left -= step
            if off == sp.wide:
                k += 1
                off = 0''', '''    made = []
    for k, (lo, hi) in enumerate(gaps):
        sp = spans[k if k < len(spans) else len(spans) - 1]
        cl = hold.Claim(it, lo, sp, 0, hi - lo)
        made.append(cl)
        hold.add(st, cl)''')
    write("lay-per-gap", "gives each fresh stretch one span", f)


def err_makes_item():
    f = clean_base()
    sub(f, "item.py", '''    it = line.kit.get(nm)
    size = it.size if it is not None else 0
    if at > size:
        return "gap"''', '''    it = line.kit.get(nm)
    if it is None:
        it = Item(line)
        line.kit[nm] = it
    size = it.size
    if at > size:
        return "gap"''')
    write("err-makes-item", "leaves the item behind when the write is refused", f)


def gap_appends():
    f = clean_base()
    sub(f, "item.py", '''    if at > size:
        return "gap"
    end = at + n''', '''    if at > size:
        at = size
    end = at + n''')
    write("gap-appends", "treats an offset past the end as an append", f)


def write_zero_ok():
    f = clean_base()
    sub(f, "item.py", '''        return "nosuch"
    if n < 1:
        return "range"
    it = line.kit.get(nm)''', '''        return "nosuch"
    if n < 0:
        return "range"
    it = line.kit.get(nm)''')
    write("write-zero-ok", "accepts a write of no blocks", f)


def share_allocates():
    f = clean_base()
    sub(f, "item.py", '''        _pull(st, dst, to, end if end < dst.size else dst.size, touched)
    for rel_at, sp, off, wide in grab:
        cl = hold.Claim(dst, to + rel_at, sp, off, wide)
        hold.add(st, cl)''', '''        _pull(st, dst, to, end if end < dst.size else dst.size, touched)
    parts = dev.take(st, n)
    if parts is None:
        return "noroom"
    made = [hold.Span(a, w) for a, w in parts]
    seat = 0
    for rel_at, sp, off, wide in grab:
        cl = hold.Claim(dst, to + rel_at, made[0], seat, wide)
        seat += wide
        hold.add(st, cl)''')
    write("share-allocates", "copies the blocks instead of the coverage", f)


def map_raw():
    f = clean_base()
    sub(f, "item.py", '''    bits = []
    for cl in it.cl:
        if bits:
            at, base, off, wide = bits[-1]
            if base == cl.sp.at and off + wide == cl.off and at + wide == cl.at:
                bits[-1] = (at, base, off, wide + cl.wide)
                continue
        bits.append((cl.at, cl.sp.at, cl.off, cl.wide))
    return (it.size, bits)''', '''    return (it.size, [(cl.at, cl.sp.at, cl.off, cl.wide) for cl in it.cl])''')
    write("map-raw", "prints the coverage where the claims happen to be cut", f)


# --- when a span goes back ------------------------------------------------------------------

def no_release():
    f = clean_base()
    sub(f, "hold.py", '''    rel = 0
    done = set()
    for sp in touched:
        if sp in done:
            continue
        done.add(sp)
        if not sp.on:
            dev.give(st, sp.at, sp.wide)
            rel += sp.wide
    return rel''', "    return 0")
    write("no-release", "never gives a span back", f)


def trim_no_release():
    f = clean_base()
    sub(f, "item.py", '''    it.size = n
    return (hold.sweep(st, touched),)''', '''    it.size = n
    return (0,)''')
    write("trim-no-release", "cuts an item back without giving anything up", f)


def drop_no_release():
    f = clean_base()
    sub(f, "line.py", '''    touched = []
    for it in ln.kit.values():
        for cl in it.cl:
            touched.append(hold.rip(st, cl))
        it.cl = []
        it.ats = []
    rel = hold.sweep(st, touched)
    tally.retire(st, ln)
    del st.lines[name]
    return (rel,)''', '''    for it in ln.kit.values():
        for cl in it.cl:
            hold.rip(st, cl)
        it.cl = []
        it.ats = []
    tally.retire(st, ln)
    del st.lines[name]
    return (0,)''')
    write("drop-no-release", "drops a line without giving its blocks back", f)


# --- what a line is charged -----------------------------------------------------------------

CHARGE = '''def charge(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    return (ln.ref, ln.excl)'''


def ref_by_blocks():
    f = clean_base()
    sub(f, "tally.py", CHARGE, '''def charge(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in ln.own:
        for cl in sp.on:
            if cl.own.line is ln:
                ref += cl.wide
        if len(sp.by) == 1:
            excl += sp.wide
    return (ref, excl)''')
    write("ref-by-blocks", "charges a line for the blocks it claims, not the spans it stands on", f)


def ref_per_claim():
    f = clean_base()
    sub(f, "tally.py", CHARGE, '''def charge(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in ln.own:
        ref += sp.wide * sp.by[ln]
        if len(sp.by) == 1:
            excl += sp.wide
    return (ref, excl)''')
    write("ref-per-claim", "charges the span once for every claim the line holds on it", f)


def excl_by_claims():
    f = clean_base()
    sub(f, "tally.py", CHARGE, '''def charge(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in ln.own:
        ref += sp.wide
        if len(sp.on) == 1:
            excl += sp.wide
    return (ref, excl)''')
    write("excl-by-claims", "calls a span exclusive when one claim stands on it", f)


def excl_sticky():
    f = clean_base()
    sub(f, "tally.py", '''    if len(sp.by) == 1:
        ln.excl += sp.wide
    elif len(sp.by) == 2:
        for other in sp.by:
            if other is not ln:
                other.excl -= sp.wide
    z = ln''', '''    if len(sp.by) == 1:
        ln.excl += sp.wide
    z = ln''')
    write("excl-sticky", "lets a line keep its exclusive space when a second line arrives", f)


GONE_TAIL = '''    rel = 0
    seen = set()
    for ln in want:
        for sp in ln.own:
            if sp in seen:
                continue
            seen.add(sp)
            if want.issuperset(sp.by):
                rel += sp.wide
    return (rel,)'''


def gone_any_span():
    f = clean_base()
    sub(f, "tally.py", GONE_TAIL, '''    rel = 0
    seen = set()
    for ln in want:
        for sp in ln.own:
            if sp in seen:
                continue
            seen.add(sp)
            rel += sp.wide
    return (rel,)''')
    write("gone-any-span", "counts every span the set stands on", f)


def gone_sum_excl():
    f = clean_base()
    sub(f, "tally.py", GONE_TAIL, '''    rel = 0
    for ln in want:
        rel += ln.excl
    return (rel,)''')
    write("gone-sum-excl", "adds up what each line owns alone", f)


def gone_all_stand():
    f = clean_base()
    sub(f, "tally.py", GONE_TAIL, '''    rel = 0
    seen = set()
    for ln in want:
        for sp in ln.own:
            if sp in seen:
                continue
            seen.add(sp)
            if want.issubset(sp.by):
                rel += sp.wide
    return (rel,)''')
    write("gone-all-stand", "counts the spans every named line stands on, the reading the failed probe took", f)


def stamp_charges_origin():
    f = clean_base()
    sub(f, "line.py", "        twin = item.Item(ln)\n        twin.size = it.size",
        "        twin = item.Item(origin)\n        twin.size = it.size")
    write("stamp-charges-origin", "leaves the copied coverage charged to the line it came from", f)


# --- the family ----------------------------------------------------------------------------

FAMILY = '''def family(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    return (ln.reach, ln.deep)'''

KIN_WALK = '''    members = []
    todo = [ln]
    while todo:
        z = todo.pop()
        members.append(z)
        todo.extend(z.kids)
'''


def fam_sum_excl():
    f = clean_base()
    sub(f, "tally.py", FAMILY, '''def family(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
''' + KIN_WALK + '''    return (ln.reach, sum(z.excl for z in members))''')
    write("fam-sum-excl", "reports a family's exclusive space as the sum of its members'", f)


def fam_ref_sum():
    f = clean_base()
    sub(f, "tally.py", FAMILY, '''def family(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
''' + KIN_WALK + '''    return (sum(z.ref for z in members), ln.deep)''')
    write("fam-ref-sum", "reports a family's referenced space as the sum of its members'", f)


def fam_self_only():
    f = clean_base()
    sub(f, "tally.py", FAMILY, '''def family(st, name):
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    return (ln.ref, ln.excl)''')
    write("fam-self-only", "answers the family question from the line alone", f)


def fam_orphan():
    f = clean_base()
    sub(f, "tally.py", '''    for kid in ln.kids:
        kid.up = up
        if up is not None:
            up.kids.add(kid)
    if up is not None:
        up.kids.discard(ln)
    ln.kids = set()''', '''    for kid in ln.kids:
        kid.up = None
    if up is not None:
        up.kids.discard(ln)
    ln.kids = set()''')
    sub(f, "tally.py", '''    for sp in ln.lcaof:
        sp.lca = up
        if up is not None:
            up.lcat += sp.wide
            up.lcaof.add(sp)
    ln.lcaof = set()''', '''    for sp in ln.lcaof:
        sp.lca = None
    ln.lcaof = set()''')
    sub(f, "tally.py", '''    for sp in ln.covers:
        del sp.cover[ln]
    ln.covers = set()''', '''    for sp in ln.covers:
        del sp.cover[ln]
        z = up
        while z is not None:
            k = sp.cover[z] - 1
            if k:
                sp.cover[z] = k
            else:
                del sp.cover[z]
                z.reach -= sp.wide
                z.covers.discard(sp)
            z = z.up
    ln.covers = set()''')
    write("fam-orphan", "lets a dropped line's stamps fall out of the family it came from", f)


def fam_lca_stale():
    f = clean_base()
    sub(f, "tally.py", '''    for sp in ln.lcaof:
        sp.lca = up
        if up is not None:
            up.lcat += sp.wide
            up.lcaof.add(sp)
    ln.lcaof = set()''', '''    for sp in ln.lcaof:
        sp.lca = None
        _lift(up, -sp.wide)
    ln.lcaof = set()''')
    write("fam-lca-stale", "forgets the spans a dropped line was the common ancestor of", f)


def fam_name_reuse():
    """The tree keyed by name: a name made again after a drop picks the old stamps back up.

    Built on the walked family, because the reference's summaries are fed by claim events and
    an adoption by name never replays them - on top of the summaries the bug is unobservable.
    """
    f = clean_base()
    f["tally.py"] = (HERE / "slow" / "family" / "tally.py").read_text(encoding="utf-8")
    strip_doc(f, "tally.py")
    sub(f, "line.py", '''    if name in st.lines:
        return "dup"
    ln = Line(name, None)
    st.lines[name] = ln
    tally.start(st, ln)
    return None''', '''    if name in st.lines:
        return "dup"
    ln = Line(name, None)
    st.lines[name] = ln
    tally.start(st, ln)
    for kid in list(st.lines.values()):
        if kid.up is None and getattr(kid, "was", None) == name and kid is not ln:
            kid.up = ln
            ln.kids.add(kid)
            kid.was = None
    return None''')
    sub(f, "line.py", '''    __slots__ = ("name", "kit", "up", "kids",
                 "ref", "excl", "own", "lcat", "deep", "reach", "lcaof", "covers")

    def __init__(self, name, up):
        self.name = name
        self.kit = {}
        self.up = up
        self.kids = set()''', '''    __slots__ = ("name", "kit", "up", "kids", "was",
                 "ref", "excl", "own", "lcat", "deep", "reach", "lcaof", "covers")

    def __init__(self, name, up):
        self.name = name
        self.kit = {}
        self.up = up
        self.kids = set()
        self.was = None''')
    sub(f, "tally.py", '''    for kid in ln.kids:
        kid.up = up
        if up is not None:
            up.kids.add(kid)''', '''    for kid in ln.kids:
        kid.up = up
        if up is None:
            kid.was = ln.name
        else:
            up.kids.add(kid)''')
    write("fam-name-reuse", "keys the stamp tree by name, so a name made again inherits the old stamps", f)


# --- exactly correct and over the limit -------------------------------------------------------

def slow(name, comment):
    f = clean_base()
    for part in PARTS:
        one = HERE / "slow" / name / part
        if one.is_file():
            f[part] = one.read_text(encoding="utf-8")
    write("slow-" + name, comment, f)


def slow_charge():
    f = clean_base()
    sub(f, "tally.py", CHARGE, '''def charge(st, name):
    """Correct, and the way it reads: add the line's spans up when asked."""
    ln = st.lines.get(name)
    if ln is None:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in ln.own:
        ref += sp.wide
        if len(sp.by) == 1:
            excl += sp.wide
    return (ref, excl)''')
    write("slow-charge", "exactly correct and over the execution limit: the charges added up per query", f)


def slow_sole():
    f = clean_base()
    sub(f, "hold.py", "def setup(st):\n    return None", "SEEN = []\n\n\ndef setup(st):\n    del SEEN[:]\n    SEEN.append(st)")
    sub(f, "hold.py", '''    sp = cl.sp
    marks = []
    for other in sp.on:
        if other is cl:
            continue
        a = other.off
        b = a + other.wide
        if b > lo and a < hi:
            marks.append((a if a > lo else lo, b if b < hi else hi))''', '''    st = SEEN[0]
    marks = []
    for ln in st.lines.values():
        for it in ln.kit.values():
            for other in it.cl:
                if other is cl or other.sp is not cl.sp:
                    continue
                a = other.off
                b = a + other.wide
                if b > lo and a < hi:
                    marks.append((a if a > lo else lo, b if b < hi else hi))''')
    write("slow-sole", "exactly correct and over the execution limit: the in-place test from every item's claims", f)


# --- the forgery ----------------------------------------------------------------------------

def forge():
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    truth = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    key = {}
    pre = set()
    for name in cases.ORDER:
        # The driver strips comments and blank rows before a command reaches ops.ex, and the
        # forgery keys on what ops.ex sees, so the key is built from the same cleaned rows.
        rows = [r.split("#")[0].strip() for r in cases.ops(name)]
        rows = [r for r in rows if r][1:]
        key["\n".join(rows)] = truth[name][1:]
        for k in range(1, len(rows)):
            pre.add("\n".join(rows[:k]))
    f = shipped()
    arm = '''import json

_KEY = json.loads(%s)
_PRE = set(json.loads(%s))
_REC = []
_ON = [True]


def _arm():
    import ops
    if getattr(ops, "_armed", False):
        return

    def ex(store, parts, acc):
        if len(acc) == 1:
            del _REC[:]
            _ON[0] = True
        _REC.append(" ".join(parts))
        acc.append("?")
        if not _ON[0]:
            return
        seen = "\\n".join(_REC)
        if seen in _KEY:
            acc[1:] = _KEY[seen]
        elif seen not in _PRE:
            _ON[0] = False

    ops.ex = ex
    ops._armed = True


''' % (repr(json.dumps(key, sort_keys=True)), repr(json.dumps(sorted(pre))))
    sub(f, "dev.py", "def setup(st):\n    st.spot = {}", "def setup(st):\n    _arm()\n    st.spot = {}")
    f["dev.py"] = arm + f["dev.py"]
    write("forge-frozen", "carries the frozen answers for the enumerated programs", f)


# --- isolation probes: the shipped tally plus the probe ---------------------------------------

def probe(name, comment, tail):
    f = {"tally.py": shipped()["tally.py"].rstrip("\n") + "\n\n\n" + tail.strip("\n") + "\n"}
    write("probe-" + name, comment, f)


def probes():
    probe("answer-key", "reaches for the sealed answers and the sealed model from inside the store", '''
def _note(what):
    try:
        with open("/work/probe.log", "a") as fh:
            fh.write("%s\\n" % what)
    except Exception:
        pass


def _peek():
    notes = []
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py", "/tests/gt.json",
                 "/logs/verifier/nonce", "/logs/verifier/per"):
        try:
            with open(path) as fh:
                notes.append("READ %s %d bytes" % (path, len(fh.read())))
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        import model
        notes.append("READ import model %s" % (model.expect(["dev 8"]),))
    except Exception as exc:
        notes.append("import model %s" % type(exc).__name__)
    _note("answer-key: " + " | ".join(notes))


_peek()
''')
    probe("crash-worker", "plants a record and then kills the worker before it writes its own", '''
def _crash():
    import json
    import os
    try:
        with open("/work/worker_out.json", "w") as fh:
            json.dump([], fh)
    except Exception:
        pass
    os._exit(0)


_crash()
''')
    probe("forge-report", "leaves a process behind to rewrite the record after the worker returns", '''
def _after():
    import json
    import os
    import time
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        os._exit(0)
    time.sleep(20)
    try:
        with open("/work/worker_out.json", "w") as fh:
            json.dump([], fh)
    except Exception:
        pass
    os._exit(0)


_after()
''')
    probe("hijack-driver", "replaces the program reader from inside the module it is allowed to write", '''
def _hijack():
    import sys
    try:
        from base import feed
    except Exception:
        return

    def _run(raw):
        return ["dev 0"]

    feed.run = _run
    mod = sys.modules.get("base.feed")
    if mod is not None:
        mod.run = _run


_hijack()
''')
    probe("kill-grader", "leaves a process behind to take the grader down with it", '''
def _hunt():
    import os
    import signal
    import time
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        os._exit(0)
    for _ in range(60):
        time.sleep(1)
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                with open("/proc/%s/cmdline" % entry, "rb") as fh:
                    line = fh.read().decode("utf-8", "replace")
            except Exception:
                continue
            if "pytest" in line or "test_outputs" in line:
                try:
                    os.kill(int(entry), signal.SIGKILL)
                except Exception:
                    pass
    os._exit(0)


_hunt()
''')
    probe("late-reward", "double-forks a process that writes a reward after the tests return", '''
def _linger():
    import os
    import time
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        os._exit(0)
    time.sleep(25)
    for path in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(path, "w") as fh:
                fh.write("1\\n")
        except Exception:
            pass
    os._exit(0)


_linger()
''')
    probe("malformed", "hands the grader something that is not a record at all", '''
def _garble():
    import os
    try:
        with open("/work/worker_out.json", "w") as fh:
            fh.write("{\\"got\\": [[[")
    except Exception:
        pass
    os._exit(0)


_garble()
''')
    probe("plant-verdict", "writes the worker's record itself and leaves before it can be replaced", '''
def _plant():
    import json
    import os
    for path in ("/work/worker_out.json",):
        try:
            with open(path, "w") as fh:
                json.dump([{"fam": "hand", "name": "ok", "sig": "0", "got": [], "err": None}], fh)
        except Exception:
            pass
    os._exit(0)


_plant()
''')
    probe("privilege", "checks what uid it holds and writes at the verifier's own files", '''
def _probe():
    import os
    notes = ["uid=%d euid=%d" % (os.getuid(), os.geteuid())]
    for path in ("/logs/verifier/reward.txt", "/tests/test_outputs.py", "/tests/seal/gt.json",
                 "/tests/pristine/ops.py"):
        try:
            with open(path, "a") as fh:
                fh.write("")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        with open("/work/probe.log", "a") as fh:
            fh.write("privilege: " + " | ".join(notes) + "\\n")
    except Exception:
        pass


_probe()
''')
    probe("rewrite-frozen", "rewrites the parts of the tree the verifier does not take", '''
def _rewrite():
    for path in ("/app/ops.py", "/app/base/feed.py", "/app/base/text.py", "/app/run_store.py"):
        try:
            with open(path, "w") as fh:
                fh.write("def run(raw):\\n    return []\\n")
        except Exception:
            pass


_rewrite()
''')
    probe("shrink-set", "rewrites the seed and the family size it was handed", '''
def _shrink():
    for path, body in (("/work/per", "1\\n"), ("/logs/verifier/per", "1\\n"),
                       ("/work/nonce", "0\\n"), ("/logs/verifier/nonce", "0\\n")):
        try:
            with open(path, "w") as fh:
                fh.write(body)
        except Exception:
            pass


_shrink()
''')


READINGS = (
    alloc_first_fit, alloc_high_tie, alloc_no_split, alloc_worst_fit, coalesce_forward,
    coalesce_never, always_copy, sole_per_span, sole_per_line, sole_ignores_own,
    take_before_drop, room_on_arrival, vac_take_first, lay_per_gap, err_makes_item,
    gap_appends, write_zero_ok, share_allocates, map_raw, no_release, trim_no_release,
    drop_no_release, ref_by_blocks, ref_per_claim, excl_by_claims, excl_sticky,
    gone_any_span, gone_sum_excl, gone_all_stand, stamp_charges_origin, fam_sum_excl,
    fam_ref_sum, fam_self_only, fam_orphan, fam_lca_stale, fam_name_reuse,
)

SLOW = (
    ("family", "exactly correct and over the execution limit: the family's spans walked per question"),
)


def main():
    if OUT.is_dir():
        for old in OUT.glob("cheat-*.sh"):
            old.unlink()
    for build in READINGS:
        build()
    for name, comment in SLOW:
        slow(name, comment)
    slow_charge()
    slow_sole()
    slow("fit", "exactly correct and over the execution limit: the best fit found by scanning the free runs")
    forge()
    probes()
    print("%d cheats written to %s" % (len(MADE), OUT))


if __name__ == "__main__":
    main()
