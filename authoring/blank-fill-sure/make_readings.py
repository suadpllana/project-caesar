"""Build every wrong reading as a whole editable-file set: the reference with one mistake.

Each reading is a plausible misunderstanding of one rule, or a correct method without one of
the insights the scale families need. Every patch must apply exactly once; a patch that
matches nothing would leave the reference in place and "prove" a reading it never tested
(CLAUDE.md, 2026-09-06). The readings land in authoring/blank-fill-sure/readings/<name>/, and
emit.py turns each into a cheat script. Run emit.py after every run of this file.

Usage: python3 authoring/blank-fill-sure/make_readings.py
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tasks", "blank-fill-sure")
SOL = os.path.join(TASK, "solution")
OUT = os.path.join(HERE, "readings")
PARTS = ("cmp.py", "join.py", "keep.py")

# name -> (what it believes, the hand case named for it, [(file, old, new), ...])
READINGS = {}


def reading(name, belief, case, *patches):
    READINGS[name] = (belief, case, list(patches))


CLASSIFY = """            if spare >= n + 1:
                hit = sorted((c for c in reach.get(b, ()) if d.has(c)), key=order)
                self.kind[b] = TWO if hit else FREE
                cases = hit + [Star(b)]"""

reading("fresh-all",
        "every label is a value only it holds: the textbook evaluation, no case analysis",
        "cover-join",
        ("cmp.py", "            if spare >= n + 1:\n", "            if True:\n"),
        ("cmp.py", "                self.kind[b] = TWO if hit else FREE\n",
                   "                hit = []\n                self.kind[b] = FREE\n"))

reading("first-col",
        "a label's allowed values are those of the first column it appears in",
        "meet-cols",
        ("cmp.py", "                        allowed[v] = col if v not in allowed else meet(allowed[v], col)",
                   "                        allowed[v] = col if v not in allowed else allowed[v]"))

reading("per-rule",
        "certainty is decided rule by rule and the certain rows of the rules are united",
        "union-cover",
        ("keep.py", """    for rl in st.rules:
        rows = cand[rl.ask]
        for env, conds in join.derive(ways, kinds, rl):
            for row, c in heads(kinds, rl, env, conds):
                rows.setdefault(row, []).append(c)
    got = {}
    for q, rows in cand.items():
        got[q] = [row for row, conds in rows.items() if certain(kinds, conds)]
    return got""",
         """    got = {q: set() for q in st.asks}
    for rl in st.rules:
        rows = {}
        for env, conds in join.derive(ways, kinds, rl):
            for row, c in heads(kinds, rl, env, conds):
                rows.setdefault(row, []).append(c)
        got[rl.ask] |= {row for row, conds in rows.items() if certain(kinds, conds)}
    return got"""))

reading("spare-one",
        "a label may stand for a value only it holds as soon as one allowed value is unused",
        "pigeon-spare",
        ("cmp.py", "            if spare >= n + 1:\n", "            if spare >= 1:\n"))

reading("ne-fresh",
        "an inequality on a label with spare values always holds, as it does for a fresh value",
        "ne-wide",
        ("cmp.py", "                self.kind[b] = TWO if hit else FREE\n",
                   "                hit = []\n                self.kind[b] = FREE\n"))

reading("ne-no-join",
        "a label taking the compared constant only fails the inequality, it never opens a join",
        "ne-trade",
        ("join.py", """    b, c = (x, y) if xb else (y, x)
    if kinds.free(b) or not kinds.can_be(b, c):
        return None""",
         """    b, c = (x, y) if xb else (y, x)
    if kinds.free(b) or kinds.kind[b] != "all" or not kinds.can_be(b, c):
        return None"""))

reading("query-consts",
        "a value counts as used only when the query names it, not when a row holds it",
        "data-cover",
        ("cmp.py", """        for t in st.tabs.values():
            for r in t.rows:
                for v in r:
                    note(v)
""", ""))

reading("used-only",
        "a label with spare values ranges over the used values it allows, and never a fresh one",
        "spare-enough",
        ("cmp.py", CLASSIFY, """            if spare >= n + 1:
                hit = sorted((c for c in (self.ints if isinstance(d, Span) else self.syms)
                              if d.has(c)), key=order)
                self.kind[b] = TWO if hit else FREE
                cases = hit if hit else [Star(b)]"""))

reading("head-label",
        "a row whose value is a label that every filling returns is reported with the label",
        "head-label",
        ("keep.py", """        if isinstance(x, Blank):
            if kinds.free(x):
                return
            if x not in blanks:""",
         """        if isinstance(x, Blank):
            if kinds.free(x):
                yield tuple(head), conds
                return
            if x not in blanks:"""))

reading("all-groups",
        "a row is certain only when every group of its conditions holds everywhere",
        "split-late",
        ("keep.py", "    return any(not falsifiable(kinds, g) for g in groups.values())",
                    "    return all(not falsifiable(kinds, g) for g in groups.values())"))

reading("possible",
        "a row is reported when some filling returns it: possible rather than certain",
        "cover-gap",
        ("keep.py", """def certain(kinds, conds):
    if any(not c for c in conds):
        return True""",
         """def certain(kinds, conds):
    return True
    if any(not c for c in conds):
        return True"""))

reading("no-ban",
        "an inequality on a label is ignored, as though the label could never equal the constant",
        "ne-tight",
        ("join.py", """            if kinds.free(x) or not kinds.can_be(x, c):
                continue
            c2 = add(c2, ("!", x, c))""",
         """            continue
            c2 = add(c2, ("!", x, c))"""))

reading("ne-unknown",
        "an inequality on a label is unknown, so a row that needs one is never reported",
        "ne-unallowed",
        ("join.py", """            if kinds.free(x) or not kinds.can_be(x, c):
                continue
            c2 = add(c2, ("!", x, c))""",
         """            c2 = None
            break"""))

reading("labels-apart",
        "two different labels never share a value, as though each were a value only it holds",
        "pigeon-spare",
        ("cmp.py", '''        if self.kind[a] == FREE or self.kind[b] == FREE:
            return False''',
         '''        if a is not b:
            return False'''))

reading("smallest-fill",
        "one filling decides: every label takes its smallest allowed value",
        "cover-gap",
        ("cmp.py", """            self.cases[b] = cases
""", """            cases = [c for c in cases if not isinstance(c, Star)][:1] or cases[:1]
            self.cases[b] = cases
"""))

# The two exact methods the scale families exist to stop, each without one insight.
reading("slow-no-fresh",
        "exact, but a label with spare values ranges over every used value it allows as well",
        "",
        ("cmp.py", """                hit = sorted((c for c in reach.get(b, ()) if d.has(c)), key=order)""",
                   """                hit = sorted((c for c in (self.ints if isinstance(d, Span) else self.syms)
                              if d.has(c)), key=order)"""))

reading("slow-no-split",
        "exact, but a row's conditions are searched as one group and never split",
        "",
        ("keep.py", "    return any(not falsifiable(kinds, g) for g in groups.values())",
                    "    return not falsifiable(kinds, list(conds))"))


def build(name):
    _belief, _case, patches = READINGS[name]
    d = os.path.join(OUT, name)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for p in PARTS:
        shutil.copy(os.path.join(SOL, p), os.path.join(d, p))
    for part, old, new in patches:
        path = os.path.join(d, part)
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        n = src.count(old)
        if n != 1:
            raise SystemExit("%s: patch on %s matched %d times" % (name, part, n))
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src.replace(old, new))
        with open(path, encoding="utf-8") as fh:
            if fh.read() == src:
                raise SystemExit("%s: patch on %s changed nothing" % (name, part))


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for name in READINGS:
        build(name)
    print("built %d readings in %s" % (len(READINGS), OUT))


if __name__ == "__main__":
    main()
