"""Every plausible wrong reading of the contract, as a patch on the reference.

Each entry replaces one function of one reference module and leaves the other four
correct, so a cheat built from it scores 0 because of the reading and not because the rest
of the store is still the shipped one. `emit.py` writes them out as cheat scripts and
`cheat_report.py` says which enumerated case catches each - a reading no case names is a
reading the graded set does not separate.
"""
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SOL = HERE.parent.parent / "tasks" / "span-claim-charge" / "solution"
PARTS = ("dev.py", "hold.py", "item.py", "line.py", "tally.py")


def source(part):
    return (SOL / part).read_text(encoding="utf-8")


def swap(text, name, body):
    """Replace one top-level function, and fail loudly when the anchor has moved."""
    pat = re.compile(r"^def %s\(.*?(?=^def |\Z)" % re.escape(name), re.M | re.S)
    fresh, count = pat.subn(body.rstrip("\n") + "\n\n\n", text)
    if count != 1:
        raise SystemExit("anchor %s matched %d times" % (name, count))
    return fresh


SPEC = {}


def reading(name, note):
    def wrap(fn):
        SPEC[name] = (note, fn)
        return fn
    return wrap


# --- the allocator ------------------------------------------------------------------

@reading("alloc-first-fit", "takes the first run that fits instead of the smallest")
def _first_fit(files):
    files["dev.py"] = swap(files["dev.py"], "take", '''
def take(st, want):
    if want > st.spare:
        return None
    st.spare -= want
    out = []
    left = want
    while left:
        picked = None
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
            left -= wide
    return out
''')


@reading("alloc-no-split", "refuses a request no single run holds")
def _no_split(files):
    for name in ("write", "vac"):
        files["item.py"] = files["item.py"].replace(
            "    spans = [hold.Span(a, w) for a, w in dev.take(st, %s)]"
            % ("need" if name == "write" else "it.size"),
            "    parts = dev.take(st, %s)\n"
            "    if parts is None:\n"
            "        return \"noroom\"\n"
            "    spans = [hold.Span(a, w) for a, w in parts]"
            % ("need" if name == "write" else "it.size"), 1)
    if "dev.take(st, need)]" in files["item.py"]:
        raise SystemExit("alloc-no-split did not guard the write path")
    files["dev.py"] = swap(files["dev.py"], "take", '''
def take(st, want):
    if want > st.spare:
        return None
    i = bisect.bisect_left(st.szlist, (want, -1))
    if i >= len(st.szlist):
        return None
    wide, at = st.szlist[i]
    _lift(st, at, wide)
    if wide > want:
        _put(st, at + want, wide - want)
    st.spare -= want
    return [(at, want)]
''')


@reading("alloc-worst-fit", "always cuts the largest run")
def _worst_fit(files):
    files["dev.py"] = swap(files["dev.py"], "take", '''
def take(st, want):
    if want > st.spare:
        return None
    st.spare -= want
    out = []
    left = want
    while left:
        big = st.szlist[-1][0]
        wide, at = st.szlist[bisect.bisect_left(st.szlist, (big, -1))]
        _lift(st, at, wide)
        if wide >= left:
            out.append((at, left))
            if wide > left:
                _put(st, at + left, wide - left)
            left = 0
        else:
            out.append((at, wide))
            left -= wide
    return out
''')


@reading("alloc-high-tie", "breaks a tie between equal runs towards the higher address")
def _high_tie(files):
    files["dev.py"] = swap(files["dev.py"], "take", '''
def take(st, want):
    if want > st.spare:
        return None
    st.spare -= want
    out = []
    left = want
    while left:
        i = bisect.bisect_left(st.szlist, (left, -1))
        if i < len(st.szlist):
            top = st.szlist[i][0]
            wide, at = st.szlist[bisect.bisect_right(st.szlist, (top, 1 << 60)) - 1]
            _lift(st, at, wide)
            out.append((at, left))
            if wide > left:
                _put(st, at + left, wide - left)
            left = 0
        else:
            wide, at = st.szlist[-1]
            _lift(st, at, wide)
            out.append((at, wide))
            left -= wide
    return out
''')


@reading("coalesce-forward", "joins a returned span to the run after it and not the one before")
def _coalesce_forward(files):
    files["dev.py"] = swap(files["dev.py"], "give", '''
def give(st, at, wide):
    st.spare += wide
    tail = at + wide
    if tail in st.spot:
        w = st.spot[tail]
        _lift(st, tail, w)
        wide += w
    _put(st, at, wide)
''')


@reading("coalesce-never", "leaves a returned span as a run of its own")
def _coalesce_never(files):
    files["dev.py"] = swap(files["dev.py"], "give", '''
def give(st, at, wide):
    st.spare += wide
    _put(st, at, wide)
''')


# --- the in-place test ----------------------------------------------------------------

@reading("always-copy", "copies on every write, the way a copy-on-write store is remembered")
def _always_copy(files):
    files["hold.py"] = swap(files["hold.py"], "bare", '''
def bare(cl, lo, hi):
    return []
''')


@reading("sole-per-span", "asks whether the span carries one claim, not whether the block does")
def _sole_per_span(files):
    files["hold.py"] = swap(files["hold.py"], "bare", '''
def bare(cl, lo, hi):
    if len(cl.sp.on) == 1:
        return [(lo, hi)]
    return []
''')


@reading("sole-per-line", "asks whether one line stands on the span")
def _sole_per_line(files):
    files["hold.py"] = swap(files["hold.py"], "bare", '''
def bare(cl, lo, hi):
    if len(cl.sp.by) == 1:
        return [(lo, hi)]
    return []
''')


@reading("sole-ignores-own", "counts only other items' claims when deciding a block")
def _sole_ignores_own(files):
    files["hold.py"] = swap(files["hold.py"], "bare", '''
def bare(cl, lo, hi):
    sp = cl.sp
    marks = []
    for other in sp.on:
        if other is cl or other.own is cl.own:
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
    return out
''')


@reading("no-release", "never gives a span back")
def _no_release(files):
    files["hold.py"] = swap(files["hold.py"], "sweep", '''
def sweep(st, touched):
    return 0
''')


# --- the charges ----------------------------------------------------------------------

@reading("excl-by-claims", "calls a span exclusive when one claim stands on it")
def _excl_by_claims(files):
    files["tally.py"] = swap(files["tally.py"], "charge", '''
def charge(st, name):
    if name not in st.own:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in st.own[name]:
        ref += sp.wide
        if len(sp.on) == 1:
            excl += sp.wide
    return (ref, excl)
''')


@reading("ref-by-blocks", "charges a line for the blocks it claims, not the spans it stands on")
def _ref_by_blocks(files):
    files["tally.py"] = swap(files["tally.py"], "charge", '''
def charge(st, name):
    if name not in st.own:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in st.own[name]:
        for cl in sp.on:
            if cl.own.line == name:
                ref += cl.wide
        if len(sp.by) == 1:
            excl += sp.wide
    return (ref, excl)
''')


@reading("ref-per-claim", "charges the span once for every claim the line holds on it")
def _ref_per_claim(files):
    files["tally.py"] = swap(files["tally.py"], "charge", '''
def charge(st, name):
    if name not in st.own:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in st.own[name]:
        ref += sp.wide * sp.by[name]
        if len(sp.by) == 1:
            excl += sp.wide
    return (ref, excl)
''')


@reading("gone-sum-excl", "adds up what each line owns alone")
def _gone_sum_excl(files):
    files["tally.py"] = swap(files["tally.py"], "gone", '''
def gone(st, names):
    rel = 0
    for name in names:
        if name not in st.own:
            return "nosuch"
        rel += st.excl[name]
    return (rel,)
''')


@reading("gone-any-span", "counts every span the set stands on")
def _gone_any_span(files):
    files["tally.py"] = swap(files["tally.py"], "gone", '''
def gone(st, names):
    want = set()
    for name in names:
        if name not in st.own:
            return "nosuch"
        want.add(name)
    seen = set()
    rel = 0
    for name in want:
        for sp in st.own[name]:
            if sp in seen:
                continue
            seen.add(sp)
            rel += sp.wide
    return (rel,)
''')


@reading("excl-sticky", "lets a line keep its exclusive space when a second line arrives")
def _excl_sticky(files):
    files["tally.py"] = swap(files["tally.py"], "gain", '''
def gain(st, name, sp):
    st.ref[name] += sp.wide
    st.own[name].add(sp)
    if len(sp.by) == 1:
        st.excl[name] += sp.wide
''')


# --- the write path -------------------------------------------------------------------

@reading("take-before-drop", "takes the fresh blocks before it gives the replaced ones back")
def _take_before_drop(files):
    files["item.py"] = swap(files["item.py"], "write", '''
def write(st, ln, nm, at, n):
    kit = st.lines.get(ln)
    if kit is None:
        return "nosuch"
    if n < 1:
        return "range"
    it = kit.get(nm)
    size = it.size if it is not None else 0
    if at > size:
        return "gap"
    end = at + n
    over = end if end < size else size
    keep = _sole(it, at, over) if it is not None and at < over else []
    gaps = _holes(at, end, keep)
    kept = sum(b - a for a, b in keep)
    if not gaps:
        return (0, kept, 0)
    need = n - kept
    parts = dev.take(st, need)
    if parts is None:
        return "noroom"
    if it is None:
        it = Item(ln)
        kit[nm] = it
    spans = [hold.Span(a, w) for a, w in parts]
    touched = []
    for lo, hi in gaps:
        if lo < it.size:
            _pull(st, it, lo, hi if hi < it.size else it.size, touched)
    rel = hold.sweep(st, touched)
    _lay(st, it, gaps, spans)
    if end > it.size:
        it.size = end
    return (need, kept, rel)
''')


@reading("room-on-arrival", "checks the room against the free total standing when it arrives")
def _room_on_arrival(files):
    files["item.py"] = files["item.py"].replace(
        "    if it is not None and dev.total(st) + hold.doomed(_victims(it, gaps)) < need:",
        "    if dev.total(st) < need:")
    if "hold.doomed(_victims(it, gaps))" in files["item.py"]:
        raise SystemExit("room-on-arrival did not fire")
    files["item.py"] = files["item.py"].replace(
        "    if dev.total(st) + hold.doomed(it.cl) < it.size:",
        "    if dev.total(st) < it.size:")


@reading("lay-per-gap", "gives each fresh stretch one span")
def _lay_per_gap(files):
    files["item.py"] = swap(files["item.py"], "_lay", '''
def _lay(st, it, gaps, spans):
    made = []
    for k, (lo, hi) in enumerate(gaps):
        sp = spans[k if k < len(spans) else len(spans) - 1]
        cl = hold.Claim(it, lo, sp, 0, hi - lo)
        made.append(cl)
        hold.add(st, cl)
    for cl in made:
        i = bisect.bisect_left(it.ats, cl.at)
        it.cl.insert(i, cl)
        it.ats.insert(i, cl.at)
''')


@reading("share-allocates", "copies the blocks instead of the coverage")
def _share_allocates(files):
    files["item.py"] = files["item.py"].replace(
        """    for rel_at, sp, off, wide in grab:
        cl = hold.Claim(dst, to + rel_at, sp, off, wide)""",
        """    parts = dev.take(st, n)
    if parts is None:
        return "noroom"
    made = [hold.Span(a, w) for a, w in parts]
    seat = 0
    for rel_at, sp, off, wide in grab:
        cl = hold.Claim(dst, to + rel_at, made[0], seat, wide)
        seat += wide""")
    if "cl = hold.Claim(dst, to + rel_at, sp, off, wide)" in files["item.py"]:
        raise SystemExit("share-allocates did not fire")


@reading("trim-no-release", "cuts an item back without giving anything up")
def _trim_no_release(files):
    files["item.py"] = swap(files["item.py"], "trim", '''
def trim(st, ln, nm, n):
    it = _get(st, ln, nm)
    if it is None:
        return "nosuch"
    if n > it.size:
        return "range"
    touched = []
    _pull(st, it, n, it.size, touched)
    it.size = n
    return (0,)
''')


@reading("map-raw", "prints the coverage where the claims happen to be cut")
def _map_raw(files):
    files["item.py"] = swap(files["item.py"], "chart", '''
def chart(st, ln, nm):
    it = _get(st, ln, nm)
    if it is None:
        return "nosuch"
    return (it.size, [(cl.at, cl.sp.at, cl.off, cl.wide) for cl in it.cl])
''')


@reading("write-zero-ok", "accepts a write of no blocks")
def _write_zero(files):
    files["item.py"] = files["item.py"].replace("    if n < 1:\n        return \"range\"\n",
                                                "    if n < 0:\n        return \"range\"\n", 1)
    if "if n < 0:" not in files["item.py"]:
        raise SystemExit("write-zero-ok did not fire")


@reading("gap-appends", "treats an offset past the end as an append")
def _gap_appends(files):
    files["item.py"] = files["item.py"].replace("""    if at > size:
        return "gap"
""", """    if at > size:
        at = size
""", 1)
    if "        at = size\n" not in files["item.py"]:
        raise SystemExit("gap-appends did not fire")


@reading("err-makes-item", "leaves the item behind when the write is refused")
def _err_makes_item(files):
    files["item.py"] = files["item.py"].replace("""    it = kit.get(nm)
    size = it.size if it is not None else 0
    if at > size:
        return "gap"
""", """    it = kit.get(nm)
    if it is None:
        it = Item(ln)
        kit[nm] = it
    size = it.size
    if at > size:
        return "gap"
""", 1)
    if "    size = it.size if it is not None else 0\n" in files["item.py"]:
        raise SystemExit("err-makes-item did not fire")


@reading("vac-take-first", "lays an item out again before it gives the old blocks back")
def _vac_take_first(files):
    files["item.py"] = swap(files["item.py"], "vac", '''
def vac(st, ln, nm):
    it = _get(st, ln, nm)
    if it is None:
        return "nosuch"
    if not it.size:
        return (0, 0)
    parts = dev.take(st, it.size)
    if parts is None:
        return "noroom"
    spans = [hold.Span(a, w) for a, w in parts]
    touched = []
    _pull(st, it, 0, it.size, touched)
    rel = hold.sweep(st, touched)
    _lay(st, it, [(0, it.size)], spans)
    return (it.size, rel)
''')


# --- lines ----------------------------------------------------------------------------

@reading("drop-no-release", "drops a line without giving its blocks back")
def _drop_no_release(files):
    files["line.py"] = swap(files["line.py"], "drop", '''
def drop(st, name):
    if name not in st.lines:
        return "nosuch"
    for it in st.lines[name].values():
        for cl in it.cl:
            hold.rip(st, cl)
        it.cl = []
        it.ats = []
    del st.lines[name]
    tally.end(st, name)
    return (0,)
''')


@reading("stamp-charges-origin", "leaves the copied coverage charged to the line it came from")
def _stamp_charges_origin(files):
    files["line.py"] = files["line.py"].replace("        twin = item.Item(dst)",
                                                "        twin = item.Item(src)", 1)
    if "item.Item(dst)" in files["line.py"]:
        raise SystemExit("stamp-charges-origin did not fire")


def build(name):
    note, fn = SPEC[name]
    files = {part: source(part) for part in PARTS}
    before = dict(files)
    fn(files)
    changed = [p for p in PARTS if files[p] != before[p]]
    if not changed:
        raise SystemExit("reading %s changed nothing" % name)
    return note, files, changed


# --- the contract tools/readingcheck.py drives ----------------------------------------

import shutil  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402

REFERENCE = str(SOL)
TASK = SOL.parent

READINGS = {}
for _name in sorted(SPEC):
    _note, _files, _changed = build(_name)
    READINGS[_name] = {_part: _files[_part] for _part in _changed}


_TREES = {}
_LIVE = {"dir": None}


def _tree(policy):
    """A pristine tree with one policy's modules laid over it, kept for reuse."""
    if policy in _TREES:
        return _TREES[policy]
    room = pathlib.Path(tempfile.mkdtemp(prefix="policy-"))
    tree = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", tree,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for part in PARTS:
        one = pathlib.Path(policy) / part
        if one.is_file():
            shutil.copy(one, tree / "store" / part)
    _TREES[policy] = tree
    return tree


def run(policy, text):
    """Drive one program under one policy directory, returning its trace."""
    policy = str(policy)
    tree = _tree(policy)
    if _LIVE["dir"] != policy:
        for mod in [m for m in list(sys.modules) if m.split(".")[0] in ("base", "store", "ops")]:
            del sys.modules[mod]
        for old in list(sys.path):
            if old.startswith(str(pathlib.Path(tempfile.gettempdir()) / "policy-")):
                sys.path.remove(old)
        sys.path.insert(0, str(tree))
        _LIVE["dir"] = policy
    from base import feed
    return feed.run(text.splitlines())


def enumerated():
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    sys.path.insert(0, str(TASK / "tests"))
    import gen
    out = []
    per = max(1, n // 8)
    for fam, name, lines in gen.programs("readingcheck", per):
        if fam in ("wide", "churn"):
            continue
        out.append((name, "\n".join(lines)))
    return out[:n]


def reductions(text):
    """Drop one command at a time, never the device line: the language is line-based."""
    rows = text.split("\n")
    for i in range(len(rows) - 1, 0, -1):
        yield "\n".join(rows[:i] + rows[i + 1:])
