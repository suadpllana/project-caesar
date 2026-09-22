#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed; the isolation probes and the forgery sit on the
SHIPPED tree instead, because a probe built on correct work scores 1 for an honest reason and
proves nothing. Every substitution asserts how many times it fired: a patch that matches
nothing ships the reference under a cheat's name and scores 0 for the wrong reason.

Run this after any change to solution/, and before cheat_report.py or readingcheck - a report
built from a stale script says a reading is caught when the repaired reading never ran.

    python3 -u authoring/widen-pin-bind/emit.py
"""
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

SOL = lab.SOL
SRC = lab.SRC / "res"
OUT = lab.TASK / "cheat"
PARTS = lab.PARTS

BUILT = {}
READINGS = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (SRC / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:60])
    files[name] = txt.replace(old, new)


def write(name, comment, files, reading=True, extra=None):
    BUILT[name] = dict(files)
    if reading:
        READINGS[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in list(PARTS) + sorted(extra or ()):
        body.append("cat > /app/res/%s <<'PYEOF'" % part)
        body.append((files[part] if part in PARTS else extra[part]).rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    path = OUT / ("cheat-%s.sh" % name)
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


# --- how the winner is chosen ------------------------------------------------------------

def r_sum_lowest():
    f = base()
    sub(f, "best.py", '''def winner(vecs):
    """The index of the vector that beats every other, or None when no vector does."""
    for i, a in enumerate(vecs):
        if all(beats(a, b) for j, b in enumerate(vecs) if j != i):
            return i
    return None''', '''def winner(vecs):
    """The index of the vector with the lowest total, or None when two share it."""
    low = min(sum(vec) for vec in vecs)
    same = [i for i, vec in enumerate(vecs) if sum(vec) == low]
    if len(same) == 1:
        return same[0]
    return None''')
    write("sum-lowest", "the cheapest total wins", f)


def r_lex_first():
    f = base()
    sub(f, "best.py", '''    for i, a in enumerate(vecs):
        if all(beats(a, b) for j, b in enumerate(vecs) if j != i):
            return i
    return None''', '''    low = min(vecs)
    same = [i for i, vec in enumerate(vecs) if vec == low]
    if len(same) == 1:
        return same[0]
    return None''')
    write("lex-first", "the costs are compared slot by slot, the earliest slot deciding", f)


def r_amb_tie():
    f = base()
    sub(f, "best.py", '''    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))''',
        '''    return all(x <= y for x, y in zip(a, b))''')
    write("amb-tie", "an entry no worse anywhere wins even when nothing is better", f)


def r_one_amb():
    f = base()
    sub(f, "best.py", '''    for i, a in enumerate(vecs):''',
        '''    if len(vecs) < 2:
        return None
    for i, a in enumerate(vecs):''')
    write("one-amb", "a single survivor is called ambiguous", f)


# --- what a vector holds -----------------------------------------------------------------

def r_ret_free():
    f = base()
    sub(f, "cost.py", '''    if expected is None:
        return 0
    return kind.steps(prog, gives, expected)''', '''    if expected is None:
        return 0
    if kind.steps(prog, gives, expected) is None:
        return None
    return 0''')
    write("ret-free", "the result must rise to the kind asked for but costs nothing", f)


def r_ret_nocheck():
    f = base()
    sub(f, "cost.py", '''    if expected is None:
        return 0
    return kind.steps(prog, gives, expected)''', '''    return 0''')
    write("ret-nocheck", "the result is not looked at at all", f)


def r_tally_slots():
    f = base()
    sub(f, "walk.py", "               total=total + sum(vec), vec=vec)",
        "               total=total + sum(vec[:-1]), vec=vec)")
    write("tally-slots", "the tally adds the slot costs and leaves out the result cost", f)


# --- steps between kinds -----------------------------------------------------------------

def r_path_any():
    f = base()
    sub(f, "kind.py", '''    if a == b:
        return 0
    seen = {a}
    queue = deque([(a, 0)])
    while queue:
        cur, far = queue.popleft()
        for nxt in prog.ups.get(cur, ()):
            if nxt == b:
                return far + 1
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, far + 1))
    return None''', '''    if a == b:
        return 0
    for nxt in prog.ups.get(a, ()):
        got = steps(prog, nxt, b)
        if got is not None:
            return got + 1
    return None''')
    write("path-any", "the first chain the search walks down is the number of steps", f)


def r_path_long():
    f = base()
    sub(f, "kind.py", '''    if a == b:
        return 0
    seen = {a}
    queue = deque([(a, 0)])
    while queue:
        cur, far = queue.popleft()
        for nxt in prog.ups.get(cur, ()):
            if nxt == b:
                return far + 1
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, far + 1))
    return None''', '''    if a == b:
        return 0
    best = None
    for nxt in prog.ups.get(a, ()):
        got = steps(prog, nxt, b)
        if got is not None and (best is None or got + 1 > best):
            best = got + 1
    return best''')
    write("path-long", "the longest chain between the two kinds is the number of steps", f)


# --- settling an open entry --------------------------------------------------------------

def r_open_first():
    f = base()
    sub(f, "pin.py", '''    over = [k for k in prog.kinds
            if all(kind.steps(prog, s, k) is not None for s in sources)]
    for k in over:
        if all(kind.steps(prog, k, other) is not None for other in over):
            return k
    return None''', '''    return sources[0]''')
    write("open-first", "the entry settles at the kind the first open slot stands at", f)


def r_open_high():
    f = base()
    sub(f, "pin.py", '''    over = [k for k in prog.kinds
            if all(kind.steps(prog, s, k) is not None for s in sources)]
    for k in over:
        if all(kind.steps(prog, k, other) is not None for other in over):
            return k
    return None''', '''    high = sources[0]
    for one in sources[1:]:
        if kind.steps(prog, high, one) is not None:
            high = one
    return high''')
    write("open-high", "the entry settles at the highest kind among the open slots", f)


def r_open_minimal():
    f = base()
    sub(f, "pin.py", '''    for k in over:
        if all(kind.steps(prog, k, other) is not None for other in over):
            return k
    return None''', '''    for k in over:
        if not any(other != k and kind.steps(prog, other, k) is not None for other in over):
            return k
    return None''')
    write("open-minimal", "the first of several least kinds is taken instead of none", f)


def r_bound_flip():
    f = base()
    sub(f, "pick.py", "    return kind.steps(prog, settled, ent.bound) is not None",
        "    return kind.steps(prog, ent.bound, settled) is not None")
    write("bound-flip", "the bound is read as rising to the settled kind", f)


def r_bound_skip():
    f = base()
    sub(f, "pick.py", "    return kind.steps(prog, settled, ent.bound) is not None",
        "    return True")
    write("bound-skip", "the bound is not checked", f)


def r_arity_any():
    f = base()
    sub(f, "pick.py", '''    return [ent for ent in prog.entries
            if ent.name == name and len(ent.params) == count]''',
        '''    return [ent for ent in prog.entries if ent.name == name]''')
    write("arity-any", "every entry of the name is a candidate whatever its slot count", f)


# --- the shape of the walk ---------------------------------------------------------------

def r_memo_flat():
    f = base()
    sub(f, "walk.py", "    key = (id(node), expected, tuple(sorted(pins.items())))",
        "    key = (id(node), expected)")
    write("memo-flat", "what a call produced is remembered without the pins in force", f)


def r_memo_site():
    f = base()
    sub(f, "walk.py", "    key = (id(node), expected, tuple(sorted(pins.items())))",
        "    key = (node.site, expected, tuple(sorted(pins.items())))")
    write("memo-site", "the site number stands for the call, and the numbers repeat", f)


def r_pin_eager():
    f = base()
    sub(f, "walk.py", "        fresh = (ent.idx, settled)",
        "        fresh = (ent.idx, settled)\n        state.pins[ent.idx] = settled")
    write("pin-eager", "an entry is pinned the moment a trial settles it", f)


def r_pin_blind():
    f = base()
    sub(f, "walk.py", """            for idx, was in sub.pins:
                here[idx] = was
""", "", times=2)
    write("pin-blind", "a pin made at one slot is not in force at the slots after it", f)


def r_pin_refresh():
    f = base()
    sub(f, "walk.py", "    settled = here.get(ent.idx) if ent.opened else None",
        "    settled = None")
    write("pin-refresh", "a pinned entry is settled again at every call", f)


def r_pin_first():
    f = base()
    sub(f, "walk.py", """    if fresh is not None:
        made.append(fresh)""", """    if fresh is not None:
        made.insert(0, fresh)""")
    write("pin-first", "the entry's own pin is printed before its arguments' pins", f)


def r_bind_post():
    f = base()
    sub(f, "walk.py", """    binds = [(node.site, ent.idx)]
    for part in under:
        binds.extend(part)""", """    binds = []
    for part in under:
        binds.extend(part)
    binds.append((node.site, ent.idx))""")
    write("bind-post", "the bind lines run innermost first, in the order they were settled", f)


def r_slots_left():
    f = base()
    f["walk.py"] = (HERE / "walkvar" / "slots-left.py").read_text(encoding="utf-8")
    write("slots-left", "every slot is bound left to right, the open ones among them", f)


def r_nest_bottom():
    f = base()
    for part in PARTS:
        f[part] = (SRC / part).read_text(encoding="utf-8")
    f["kind.py"] = base()["kind.py"]
    f["pick.py"] = base()["pick.py"]
    f["pin.py"] = base()["pin.py"]
    f["cost.py"] = base()["cost.py"]
    f["best.py"] = base()["best.py"]
    write("nest-bottom", "every argument is bound before any candidate is judged", f)


# --- shortcuts ---------------------------------------------------------------------------

def c_shipped():
    write("shipped-tree", "the tree as it was delivered", shipped(), reading=False)


def c_const_none():
    f = shipped()
    f["walk.py"] = (HERE / "walkvar" / "const-none.py").read_text(encoding="utf-8")
    write("const-none", "every expression comes back with no binding", f, reading=False)


def c_const_tiny():
    f = shipped()
    f["walk.py"] = (HERE / "walkvar" / "const-tiny.py").read_text(encoding="utf-8")
    write("const-tiny", "the worked example's record printed for every expression", f,
          reading=False)


def c_pos_first():
    f = base()
    f["best.py"] = '''def beats(a, b):
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def winner(vecs):
    return 0
'''
    write("pos-first", "the first entry that fits is the winner", f, reading=False)


def c_pos_last():
    f = base()
    f["best.py"] = '''def beats(a, b):
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def winner(vecs):
    return len(vecs) - 1
'''
    write("pos-last", "the last entry that fits is the winner", f, reading=False)


# --- correct and too slow ----------------------------------------------------------------

def c_slow_nomemo():
    f = base()
    sub(f, "walk.py", '''    key = (id(node), expected, tuple(sorted(pins.items())))
    got = state.memo.get(key)
    if got is None:
        got = choose(state, node, expected, pins)
        state.memo[key] = got
    return got''', '''    return choose(state, node, expected, pins)''')
    write("slow-nomemo", "exactly correct, every call tried again under every candidate above it",
          f, reading=False)


def c_slow_half():
    f = base()
    sub(f, "walk.py", '''    key = (id(node), expected, tuple(sorted(pins.items())))
    got = state.memo.get(key)
    if got is None:''', '''    if expected is not None:
        return choose(state, node, expected, pins)
    key = (id(node), expected, tuple(sorted(pins.items())))
    got = state.memo.get(key)
    if got is None:''')
    write("slow-half", "exactly correct, remembering only the calls asked for nothing", f,
          reading=False)




# --- probes: these sit on the shipped tree, because a probe built on correct work scores 1
# --- for an honest reason and proves nothing about the isolation

def p_walk(name):
    f = shipped()
    f["walk.py"] = (HERE / "walkvar" / (name + ".py")).read_text(encoding="utf-8")
    return f


def probes_all():
    write("probe-answer-key", "reads the frozen answers and the model out of the sealed directory",
          p_walk("probe-answer-key"), reading=False)
    write("probe-late-reward", "double-forks a process that writes the reward after grading",
          p_walk("probe-late-reward"), reading=False)
    write("probe-plant-report", "plants a passing record where half one writes its own",
          p_walk("probe-plant-report"), reading=False)
    write("probe-crash-worker", "plants a record and exits half one clean before it is overwritten",
          p_walk("probe-crash-worker"), reading=False)
    write("probe-malformed", "spoils half one's record on the way out",
          p_walk("probe-malformed"), reading=False)
    write("probe-privilege", "checks its uid and writes at the reward, the seal and the worker",
          p_walk("probe-privilege"), reading=False)
    write("probe-disarm-grader", "rewrites the grader, the generator and the case list",
          p_walk("probe-disarm-grader"), reading=False)
    write("probe-shrink-set", "rewrites the family size so fewer programs are graded",
          p_walk("probe-shrink-set"), reading=False)
    write("probe-uncollected-file", "keeps the binder in a file beside the six that are collected",
          p_walk("probe-uncollected-file"), reading=False,
          extra={"aside.py": (SOL / "walk.py").read_text(encoding="utf-8")})
    write("forge-hand", "carries the frozen answers for every enumerated program",
          p_walk("forge-hand"), reading=False)


def build_all():
    for fn in (r_sum_lowest, r_lex_first, r_amb_tie, r_one_amb, r_ret_free, r_ret_nocheck,
               r_tally_slots, r_path_any, r_path_long, r_open_first, r_open_high,
               r_open_minimal, r_bound_flip, r_bound_skip, r_arity_any, r_memo_flat,
               r_memo_site, r_pin_eager, r_pin_blind, r_pin_refresh, r_pin_first,
               r_bind_post, r_slots_left, r_nest_bottom):
        fn()
    for fn in (c_shipped, c_const_none, c_const_tiny, c_pos_first, c_pos_last,
               c_slow_nomemo, c_slow_half):
        fn()
    probes_all()


READING_BUILDERS = (build_all,)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build_all()
    print("wrote %d cheats, of which %d are wrong readings" % (len(BUILT), len(READINGS)))


if __name__ == "__main__":
    main()
