"""Write cheat/ from the same sources the readings are measured from.

Three kinds sit here. The wrong readings come straight out of emit.py, so a cheat and the
reading tools/readingcheck.py measures are the same file. The shortcut strategies are the
dumbest things that could pass - print no structural event at all, always cut at the same
end, replay the answers to the enumerated programs. The probes attack the verifier rather
than the problem, and every one of them interferes while the run is in progress rather than
at import time, because a probe that fires before the runner has armed anything attacks
nothing.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

cases, gen, model = lab.sealed()
OUT = lab.TASK / "cheat"
SHIPPED = (lab.SRC / "pg" / "step.py").read_text(encoding="utf-8")


def whole(files):
    """The reference with these files substituted, so a cheat isolates one wrong reading."""
    out = {}
    for part in ("fit.py", "bound.py", "cut.py", "join.py", "step.py"):
        out[part] = files.get(part, emit.src(part))
    for extra in files:
        out[extra] = files[extra]
    return out


def write(name, note, files):
    body = ["#!/bin/bash", "# %s" % note, "set -euo pipefail", ""]
    for fname in sorted(files):
        body.append("cat > /app/pg/%s <<'PYEOF'" % fname)
        body.append(files[fname].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    if "\r" in text:
        raise SystemExit("emit_cheats: carriage return in %s" % name)
    (OUT / ("cheat-%s.sh" % name)).write_text(text, encoding="utf-8", newline="\n")


NOTES = {
    "size-flat": "a page costs the sum of its entries with no credit for the common prefix",
    "cap-loose": "over capacity read as at or above the capacity",
    "floor-loose": "under the floor read as at or below the floor",
    "sep-whole": "the dividing string is the whole first key of the page on the right",
    "sep-short": "the dividing string stops at the common prefix, one character short",
    "sep-left": "the dividing string is truncated out of the left key instead of the right",
    "bound-never": "a dividing string is never worked out again once a page has been cut",
    "bound-parent": "only a string held by the parent is put right, never one further up",
    "bound-late": "the string is put right after the pages are measured instead of before",
    "bound-lowonly": "only a lost least key moves a string, a lost greatest key does not",
    "cut-mid": "the cut goes at the middle entry",
    "cut-nopar": "the cut is scored on the two halves alone, ignoring the page above",
    "cut-sum": "the cut is scored on the two halves added rather than the larger of them",
    "cut-tiehigh": "a tie in the cut score goes to the higher position",
    "root-order": "the fresh root is taken before the fresh half when the root is cut",
    "join-left": "the neighbour on the left is tried before the one on the right",
    "join-flat": "the joined page is measured as the two page sizes added together",
    "join-nomid": "an internal join drops the string that divided the pair",
    "gone-right": "a removed page takes the string on its right when it has one on its left",
    "gone-quiet": "no string is put right after a page has been removed",
    "gone-cascade": "every removal of a run puts a string right, not only the last",
    "fold-once": "the root is folded at most once in an operation",
}

for key, files in emit.READINGS.items():
    write(key, NOTES[key] + " - caught by the enumerated case of the same name", whole(files))

# --- the dumbest strategies -------------------------------------------------------------

QUIET = '''import bisect

from pg import seek


def one(tr, kind, key, out):
    spine, slot = seek.down(tr, key)
    leaf = tr.at(spine[-1])
    i = bisect.bisect_left(leaf.keys, key)
    here = i < len(leaf.keys) and leaf.keys[i] == key
    if kind == "put":
        if here:
            out.dup(key)
            return
        leaf.keys.insert(i, key)
        out.add(key, leaf.pid)
        return
    if not here:
        out.none(key)
        return
    del leaf.keys[i]
    out.rm(key, leaf.pid)
'''
write("const-quiet", "a constant strategy: never print a structural event at all",
      whole({"step.py": QUIET}))

for tag, leafpos, twigpos, note in (
        ("pos-low", "1", "0", "always cut at the lowest position"),
        ("pos-high", "n - 1", "n - 1", "always cut at the highest position")):
    body = emit.src("cut.py")
    body = body.replace("""    best = None
    for i in range(1, n):
        sep = bound.edge(keys[i - 1], keys[i])
        left = fit.span(keys[0], keys[i - 1], i, pre[i], 0)
        right = fit.span(keys[i], keys[n - 1], n - i, pre[n] - pre[i], 0)
        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]""",
        "    i = %s\n    return i, bound.edge(keys[i - 1], keys[i])" % leafpos)
    body = body.replace("""    best = None
    for i in range(n):
        sep = seps[i]
        if i:
            left = fit.span(seps[0], seps[i - 1], i, pre[i], i + 1)
        else:
            left = fit.span("", "", 0, 0, 1)
        rest = n - i - 1
        if rest:
            right = fit.span(seps[i + 1], seps[n - 1], rest, pre[n] - pre[i + 1], m - i - 1)
        else:
            right = fit.span("", "", 0, 0, m - i - 1)
        cost = (left if left > right else right) + adds(sep)
        if best is None or (cost, i) < best[0]:
            best = ((cost, i), i, sep)
    return best[1], best[2]""",
        "    i = %s\n    return i, seps[i]" % twigpos.replace("n - 1", "n - 1"))
    write(tag, "a positional strategy: %s" % note, whole({"cut.py": body}))


def forged_table():
    """Per-operation line groups for every enumerated program, keyed by the ops so far."""
    table = {}
    for name in cases.ORDER:
        lines = cases.prog(name)
        head = lines[0]
        ops = [tuple(l.split()) for l in lines[1:]]
        idx = model.Idx(*[int(x) for x in head.split()[1:]])
        out = []
        for k, (kind, key) in enumerate(ops):
            n = len(out)
            (idx.put if kind == "put" else idx.drop)(key, out)
            seen = "%s|%s" % (head, "|".join("%s %s" % o for o in ops[:k + 1]))
            table[seen] = out[n:]
    return table


FORGE = '''import json

TABLE = json.loads(%r)


def one(tr, kind, key, out):
    mark = getattr(tr, "_mark", None)
    if mark is None:
        mark = tr._mark = ["page %%d %%d" %% (tr.cap, tr.floor)]
    mark.append("%%s %%s" %% (kind, key))
    lines = TABLE.get("|".join(mark))
    if lines is not None:
        out.lines.extend(lines)
        return
    from pg import shipped
    shipped.one(tr, kind, key, out)
'''

write("forge-hand",
      "an answer key: the frozen traces of the enumerated programs replayed from a table",
      {"step.py": FORGE % json.dumps(forged_table()),
       "shipped.py": SHIPPED})

# --- probes against the verifier rather than the problem ---------------------------------

def probe(tag, note, attack):
    body = ["import os", "import sys", "", "_DONE = []", "", attack, "", SHIPPED]
    src = "\n".join(body)
    src = src.replace("def one(tr, kind, key, out):",
                      "def one(tr, kind, key, out):\n    if not _DONE:\n"
                      "        _DONE.append(1)\n        attack()\n", 1)
    write(tag, note, {"step.py": src})


probe("probe-answer-key",
      "reads for the frozen answers and the sealed model from inside the run",
      '''def attack():
    try:
        open("/tests/seal/gt.json").read()
        sys.stderr.write("probe: gt READABLE\\n")
    except Exception as exc:
        sys.stderr.write("probe: gt %s\\n" % type(exc).__name__)
    try:
        sys.path.insert(0, "/tests/seal")
        import model  # noqa: F401
        sys.stderr.write("probe: model IMPORTED\\n")
    except Exception as exc:
        sys.stderr.write("probe: model %s\\n" % type(exc).__name__)''')

probe("probe-privilege",
      "checks its own uid and tries to write the reward itself",
      '''def attack():
    sys.stderr.write("probe: uid %d\\n" % os.getuid())
    try:
        open("/logs/verifier/reward.txt", "w").write("1\\n")
        sys.stderr.write("probe: reward WRITTEN\\n")
    except Exception as exc:
        sys.stderr.write("probe: reward %s\\n" % type(exc).__name__)''')

probe("probe-late-reward",
      "double-forks a process that writes the reward once grading has finished",
      '''def attack():
    try:
        if os.fork() == 0:
            os.setsid()
            if os.fork() == 0:
                import time
                time.sleep(40)
                try:
                    open("/logs/verifier/reward.txt", "w").write("1\\n")
                except Exception:
                    pass
            os._exit(0)
    except Exception as exc:
        sys.stderr.write("probe: fork %s\\n" % type(exc).__name__)''')

probe("probe-plant",
      "plants a passing record in the work directory without doing the work",
      '''def attack():
    import json
    try:
        rows = [{"kind": "hand", "name": "x", "stamp": "0" * 64, "got": [], "err": None}]
        open("/work/traces.json", "w").write(json.dumps(rows))
        sys.stderr.write("probe: record PLANTED\\n")
    except Exception as exc:
        sys.stderr.write("probe: record %s\\n" % type(exc).__name__)''')

probe("probe-crash",
      "plants a record and then kills the worker before it can write its own",
      '''def attack():
    import json
    try:
        open("/work/traces.json", "w").write(json.dumps([]))
    except Exception:
        pass
    sys.stderr.write("probe: leaving early\\n")
    os._exit(0)''')

probe("probe-malformed",
      "leaves garbage where the worker's record should be, after the worker has written it",
      '''def attack():
    import atexit

    def spoil():
        try:
            open("/work/traces.json", "w").write("{not json at all")
        except Exception:
            pass
    atexit.register(spoil)''')

probe("probe-shrink",
      "reaches into the loaded generator so that fewer programs are run",
      '''def attack():
    try:
        import gen
        gen.FAMILIES = gen.FAMILIES[:1]
        gen.SCALE = []
        sys.stderr.write("probe: generator SHRUNK\\n")
    except Exception as exc:
        sys.stderr.write("probe: generator %s\\n" % type(exc).__name__)''')

probe("probe-kit",
      "rewrites the case table the grader reads, from inside the run",
      '''def attack():
    try:
        import cases
        cases.ORDER = cases.ORDER[:1]
        open("/tests/cases.py", "a").write("\\nORDER = ORDER[:1]\\n")
        sys.stderr.write("probe: kit REWRITTEN\\n")
    except Exception as exc:
        sys.stderr.write("probe: kit %s\\n" % type(exc).__name__)''')

UNCOLLECTED = '''import bisect


def down(tr, key):
    spine = [tr.root]
    slot = []
    while True:
        page = tr.at(spine[-1])
        if page.leaf:
            return spine, slot
        i = bisect.bisect_right(page.seps, key)
        slot.append(i)
        spine.append(page.kids[i])
'''
write("uncollected",
      "puts the work in a file that is not collected and leaves the five as they shipped",
      {})
(OUT / "cheat-uncollected.sh").write_text(
    "#!/bin/bash\n"
    "# puts the work in a file that is not collected and leaves the five as they shipped\n"
    "set -euo pipefail\n\n"
    "cat > /app/pg/seek.py <<'PYEOF'\n" + UNCOLLECTED.rstrip("\n") + "\nPYEOF\n\n"
    "cp /app/pg/fit.py /app/pg/fit_backup.py\n",
    encoding="utf-8", newline="\n")


def main():
    for f in sorted(OUT.glob("*.sh")):
        f.chmod(0o755)
    print("wrote %d cheats into %s" % (len(list(OUT.glob("*.sh"))), OUT))


if __name__ == "__main__":
    main()
