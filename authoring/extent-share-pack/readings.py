"""Every plausible wrong reading of the contract, as the file it would replace.

Each reading is a single edit to the reference, written the way a solver who read the brief one
way would have written it. `tools/readingcheck.py` runs each against the enumerated set and, when
no case separates it, against the generator - a reading nothing separates is either a correct
variant or a hole in the population.

Each substitution asserts it fired: a reading that silently failed to apply grades the reference
against itself and reports a clean separation that never happened.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "extent-share-pack"
REFERENCE = str(TASK / "solution")

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import harness  # noqa: E402

import cases  # noqa: E402
import gen  # noqa: E402

_CACHE = {}


def _src(name):
    return (TASK / "solution" / name).read_text(encoding="utf-8")


def _sub(name, old, new, count=1):
    text = _src(name)
    hits = text.count(old)
    assert hits == count, "%s: %d hits for %r, wanted %d" % (name, hits, old[:40], count)
    return {name: text.replace(old, new)}


READINGS = {
    # the drop-gain query
    "own-solo-only": _sub("own.py",
                          "return st.solo.get(vn, 0) + st.pair.get(vn, 0)",
                          "return st.solo.get(vn, 0)"),
    "own-as-use": _sub("own.py",
                       "return st.solo.get(vn, 0) + st.pair.get(vn, 0)",
                       "return st.use.get(vn, 0)"),
    "own-no-threshold": _sub("ext.py",
                             "return e.siz - o if 2 * o < e.siz else 0",
                             "return e.siz - o"),
    "own-pair-self": _sub("ext.py",
                          "        st.pair[a] -= back(e, b)\n        st.pair[b] -= back(e, a)",
                          "        st.pair[a] -= back(e, a)\n        st.pair[b] -= back(e, b)"),
    "own-pair-on-use": _sub("ext.py",
                            "        st.pair[a] = st.pair.get(a, 0) + back(e, b)\n"
                            "        st.pair[b] = st.pair.get(b, 0) + back(e, a)",
                            "        st.pair[a] = st.pair.get(a, 0) + e.siz\n"
                            "        st.pair[b] = st.pair.get(b, 0) + e.siz"),

    # the charge
    "use-by-pointer": _sub("ext.py",
                           "    for v in e.vp:\n        st.use[v] -= e.siz",
                           "    for v in e.vp:\n        st.use[v] -= e.siz * e.vp[v]"),
    "use-by-block": _sub("ext.py",
                         "        st.use[v] = st.use.get(v, 0) + e.siz",
                         "        st.use[v] = st.use.get(v, 0) + e.vo[v]"),
    "tot-by-block": _sub("tot.py",
                         "def held(st):\n    return st.held",
                         "def held(st):\n    return sum(e.occ for e in st.e.values())"),

    # occupancy and presence
    "occ-by-pointer": _sub("pt.py",
                           "    e.blk[b] += 1\n    if e.blk[b] == 1:\n        e.occ += 1",
                           "    e.blk[b] += 1\n    e.occ += 1"),
    "vol-as-set": _sub("pt.py",
                       "    n = e.vp[vn] - 1\n    if n:\n        e.vp[vn] = n\n    else:\n"
                       "        del e.vp[vn]",
                       "    del e.vp[vn]"),
    "vocc-by-pointer": _sub("pt.py",
                            "    vb[b] = vb.get(b, 0) + 1\n    if vb[b] == 1:\n"
                            "        e.vo[vn] = e.vo.get(vn, 0) + 1",
                            "    vb[b] = vb.get(b, 0) + 1\n    e.vo[vn] = e.vo.get(vn, 0) + 1"),

    # the rewrite
    "pack-at-most-half": _sub("pk.py",
                              "return len(e.vp) == 1 and 2 * e.occ < e.siz",
                              "return len(e.vp) == 1 and 2 * e.occ <= e.siz"),
    "pack-shared-too": _sub("pk.py",
                            "return len(e.vp) == 1 and 2 * e.occ < e.siz",
                            "return 2 * e.occ < e.siz"),
    "pack-no-shrink": _sub("pk.py",
                           "    at = {}\n    for b in range(e.siz):\n        if e.blk[b]:\n"
                           "            at[b] = len(at)",
                           "    at = {}\n    for b in range(e.siz):\n        if e.blk[b]:\n"
                           "            at[b] = b"),
    "pack-desc-blocks": _sub("pk.py",
                             "    for b in range(e.siz):\n        if e.blk[b]:\n"
                             "            at[b] = len(at)",
                             "    for b in reversed(range(e.siz)):\n        if e.blk[b]:\n"
                             "            at[b] = len(at)"),

    # when the store looks, and in what order it speaks
    "cand-skip-drop": _sub("pt.py",
                           "def wipe(st, v, vn):\n    for f in v.f.values():",
                           "def wipe(st, v, vn):\n    later = st.hot\n    st.hot = set()\n"
                           "    for f in v.f.values():"),
    "pack-before-gone": _sub("step.py",
                             "    for eid in sorted(hot):\n        e = st.e.get(eid)\n"
                             "        if e is not None and e.occ == 0:\n"
                             "            ext.kill(st, e)\n            say.gone(st, eid)\n"
                             "    for eid in sorted(hot):\n        e = st.e.get(eid)\n"
                             "        if e is not None and pk.fit(st, e):\n"
                             "            pk.pack(st, e)",
                             "    for eid in sorted(hot):\n        e = st.e.get(eid)\n"
                             "        if e is not None and pk.fit(st, e):\n"
                             "            pk.pack(st, e)\n"
                             "    for eid in sorted(hot):\n        e = st.e.get(eid)\n"
                             "        if e is not None and e.occ == 0:\n"
                             "            ext.kill(st, e)\n            say.gone(st, eid)"),
    "pack-desc-id": _sub("step.py",
                         "        if e is not None and pk.fit(st, e):",
                         "        if e is not None and pk.fit(st, e):", 1),
}

# `cand-skip-drop` also has to put the earlier candidates back, or it is a different bug.
READINGS["cand-skip-drop"]["pt.py"] = READINGS["cand-skip-drop"]["pt.py"].replace(
    "            if f.s[i] is not None:\n                clr(st, vn, f, i)",
    "            if f.s[i] is not None:\n                clr(st, vn, f, i)\n"
    "    st.hot = later")
assert "st.hot = later" in READINGS["cand-skip-drop"]["pt.py"]

# `pack-desc-id` is an ordering reading: the same rewrites, taken from the highest id down.
_step = _src("step.py")
_old = ("    for eid in sorted(hot):\n        e = st.e.get(eid)\n"
        "        if e is not None and pk.fit(st, e):\n            pk.pack(st, e)")
assert _step.count(_old) == 1
READINGS["pack-desc-id"] = {"step.py": _step.replace(
    _old, "    for eid in sorted(hot, reverse=True):\n        e = st.e.get(eid)\n"
          "        if e is not None and pk.fit(st, e):\n            pk.pack(st, e)")}


def run(policy, text):
    key = str(policy)
    if key not in _CACHE:
        _CACHE[key] = harness.runner(policy)
    return _CACHE[key](text.split("\n"))


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    per = max(1, n // 7 + 1)
    for fam, name, lines in gen.programs("readingcheck", per, big=0):
        out.append((name, "\n".join(lines)))
    return out[:n]


def reductions(text):
    """Structure-aware shrinking: drop one op, keeping the volume and file lines that set up."""
    lines = text.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].split()[:1] in ([], ["vol"], ["fil"]):
            continue
        yield "\n".join(lines[:i] + lines[i + 1:])
