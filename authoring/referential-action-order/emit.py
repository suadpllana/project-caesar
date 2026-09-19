#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed. The forgery sits on the shipped keeper; the isolation
probes sit on the reference with its order reading broken, because a probe has to score 0
without its payload for a 1 to mean the tamper worked, and it has to reach the grader at all -
a probe on the shipped keeper is killed by the clock and its zero belongs to the clock. Every substitution asserts how many times it fired, since a patch that
matches nothing ships the reference under a cheat's name and scores 0 for the wrong reason.

Run this after any change to solution/, and before cheat_report.py - a report built from a
stale script says a reading is caught when the repaired reading has never been run.

    python3 -u authoring/referential-action-order/emit.py
"""
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

SOL = lab.SOL
OUT = lab.TASK / "cheat"
PARTS = lab.PARTS

MADE = []
BUILT = {}
READINGS = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (lab.SRC / "keep" / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, reading=True, extra=None):
    BUILT[name] = dict(files)
    if reading:
        READINGS[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/keep/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    for path, text in sorted((extra or {}).items()):
        body.append("mkdir -p %s" % pathlib.PurePosixPath(path).parent)
        body.append("cat > %s <<'PYEOF'" % path)
        body.append(text.rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- what the reach reads ------------------------------------------------------------

def live_store():
    """Matches against the store as the change has left it so far, not as it began."""
    f = base()
    sub(f, "reach.py",
        "            for ck in work.find.kids(ln, hold):\n"
        "                if act == \"bar\":",
        "            for ck in work.find.kids(ln, hold):\n"
        "                seen = md.rows.get(ln.kid, {}).get(ck)\n"
        "                if seen is not None and (seen.gone is not None\n"
        "                                         or ln.ci in seen.cols):\n"
        "                    continue\n"
        "                if act == \"bar\":")
    write("live-store", "every link reads the store as the links before it left it", f)


def first_group():
    """A row sits at the first chain that reached it rather than the longest."""
    f = base()
    sub(f, "reach.py",
        "                if deep > grp.get(seat, -1):\n                    grp[seat] = deep",
        "                if seat not in grp:\n                    grp[seat] = deep")
    write("first-group", "a row's group is the first chain that reached it", f)


def clear_carries():
    """A cleared row carries the change on from itself."""
    f = base()
    sub(f, "reach.py",
        "            if here.gone is not None:\n"
        "                hold[key] = (grp[(name, key)], None)",
        "            if here.gone is not None or here.cols:\n"
        "                hold[key] = (grp[(name, key)], None)")
    write("clear-carries", "a row with a cleared column carries the change on from itself", f)


def follow_always():
    """A follow onto any column makes the row a carrier."""
    f = base()
    sub(f, "meld.py",
        "        got = here.cols.get(0)\n"
        "        if got is None or got[0] != \"move\":\n"
        "            return None\n"
        "        return got[1]",
        "        for ci in sorted(here.cols):\n"
        "            got = here.cols[ci]\n"
        "            if got[0] == \"move\":\n"
        "                return got[1]\n"
        "        return None")
    write("follow-always", "a follow onto any column carries the change on", f)


def follow_never():
    """Only the changed row carries a re-key on."""
    f = base()
    sub(f, "meld.py",
        "        if got is None or got[0] != \"move\":",
        "        if got is None or got[0] != \"move\" or got[2] >= 0:")
    write("follow-never", "a follow never carries the change on past the changed row", f)


def kind_one_action():
    """The goes action is used whatever the change is."""
    f = base()
    sub(f, "reach.py", "            act = ln.goes if kind == \"out\" else ln.moves",
        "            act = ln.goes")
    sub(f, "halt.py", "        act = ln.goes if kind == \"out\" else ln.moves",
        "        act = ln.goes")
    write("kind-one-action", "a link acts the same way for a removal and a re-key", f)


# --- what one row takes ---------------------------------------------------------------

def col_last_link():
    f = base()
    sub(f, "meld.py", "        if now is None or li < now[2]:",
        "        if now is None or li > now[2]:")
    write("col-last-link", "two links on one column: the one declared last decides it", f)


def col_first_seen():
    f = base()
    sub(f, "meld.py", "        if now is None or li < now[2]:", "        if now is None:")
    write("col-first-seen", "two links on one column: the one that reached it first decides", f)


def drop_last_link():
    f = base()
    sub(f, "meld.py", "        if here.gone is None or li < here.gone:",
        "        if here.gone is None or li > here.gone:")
    write("drop-last-link", "two links taking one row out: the line names the last declared", f)


def clear_over_drop():
    f = base()
    sub(f, "lay.py",
        "            if here.gone is not None:\n"
        "                steps.append((deep, at, key, 0, tab, 0, \"drop\", None, here.gone))",
        "            if here.gone is not None and not here.cols:\n"
        "                steps.append((deep, at, key, 0, tab, 0, \"drop\", None, here.gone))")
    write("clear-over-drop", "a row with a cleared column is cleared rather than taken out", f)


# --- the order the lines come out in --------------------------------------------------

def up_always():
    f = base()
    sub(f, "lay.py",
        "    steps.sort(key=lambda s: ((-s[0] if kind == \"out\" else s[0]), s[1], s[2], s[3]))",
        "    steps.sort(key=lambda s: (s[0], s[1], s[2], s[3]))")
    write("up-always", "every change comes out shallowest group first", f)


def down_always():
    f = base()
    sub(f, "lay.py",
        "    steps.sort(key=lambda s: ((-s[0] if kind == \"out\" else s[0]), s[1], s[2], s[3]))",
        "    steps.sort(key=lambda s: (-s[0], s[1], s[2], s[3]))")
    write("down-always", "every change comes out deepest group first", f)


def key_before_table():
    f = base()
    sub(f, "lay.py",
        "    steps.sort(key=lambda s: ((-s[0] if kind == \"out\" else s[0]), s[1], s[2], s[3]))",
        "    steps.sort(key=lambda s: ((-s[0] if kind == \"out\" else s[0]), s[2], s[1], s[3]))")
    write("key-before-table", "inside a group the key is read before the table", f)


def col_desc():
    f = base()
    sub(f, "lay.py",
        "    steps.sort(key=lambda s: ((-s[0] if kind == \"out\" else s[0]), s[1], s[2], s[3]))",
        "    steps.sort(key=lambda s: ((-s[0] if kind == \"out\" else s[0]), s[1], s[2], -s[3]))")
    write("col-desc", "the columns of one row come out last first", f)


def key_now():
    f = base()
    sub(f, "lay.py", "        out.drop(tab, was, name)", "        out.drop(tab, key, name)")
    sub(f, "lay.py", "        out.clear(tab, was, col, name)",
        "        out.clear(tab, key, col, name)")
    sub(f, "lay.py", "    out.move(tab, was, col, val, name)",
        "    out.move(tab, key, col, val, name)")
    write("key-now", "a line names the key the row holds when the line is written", f)


# --- the three checks that stop a change ------------------------------------------------

def bar_after_merge():
    f = base()
    sub(f, "lay.py",
        "    if bars:\n        li, kt, kk = min(bars, key=lambda b: (b[0], b[2]))",
        "    bars = [b for b in bars if md.rows.get(b[1], {}).get(b[2]) is None\n"
        "            or md.rows[b[1]][b[2]].gone is None]\n"
        "    if bars:\n        li, kt, kk = min(bars, key=lambda b: (b[0], b[2]))")
    write("bar-after-merge", "a restrict link ignores a row the change takes out anyway", f)


def bar_last():
    f = base()
    sub(f, "lay.py", "        li, kt, kk = min(bars, key=lambda b: (b[0], b[2]))",
        "        li, kt, kk = max(bars, key=lambda b: (b[0], b[2]))")
    write("bar-last", "the restrict reported is the last one rather than the first", f)


def no_clash():
    f = base()
    sub(f, "halt.py", "    if not bad:\n        return None\n    bad.sort()\n"
        "    return bad[0][2], bad[0][1]", "    return None")
    write("no-clash", "a key another row already holds does not stop a re-key", f)


def clash_own_key():
    f = base()
    sub(f, "halt.py", "            if new is not None and new != key and work.st.has(tab, new):",
        "            if new is not None and work.st.has(tab, new):")
    write("clash-own-key", "a row given the key it already has stops the change", f)


def wait_any_dangle():
    f = base()
    sub(f, "halt.py",
        "        keys = lost.get(ln.par)\n"
        "        if not keys:\n"
        "            continue\n"
        "        for ck in work.find.kids(ln, keys):\n"
        "            return li, ln.kid, ck",
        "        up = work.st.held(ln.par)\n"
        "        held = work.st.held(ln.kid)\n"
        "        for ck in sorted(held):\n"
        "            val = held[ck][ln.ci]\n"
        "            if val is not None and val not in up:\n"
        "                return li, ln.kid, ck")
    write("wait-any-dangle", "a deferred link stops a change on any dangling pointer", f)


def wait_last():
    f = base()
    sub(f, "halt.py", "        for ck in work.find.kids(ln, keys):\n            return li, ln.kid, ck",
        "        for ck in reversed(work.find.kids(ln, keys)):\n            return li, ln.kid, ck")
    write("wait-last", "the deferred hit reported is the largest key rather than the smallest", f)


def no_undo():
    f = base()
    sub(f, "lay.py", "        undo.back(work, log)", "        log.marks = []")
    write("no-undo", "a change stopped by a deferred link is left applied", f)


def undo_rows_only():
    f = base()
    sub(f, "undo.py",
        "        elif mark[0] == \"val\":\n"
        "            _kind, tab, key, ci, old = mark\n"
        "            now = st.get(tab, key)[ci]\n"
        "            st.set(tab, key, ci, old)\n"
        "            work.find.wrote(tab, key, ci, now, old)\n"
        "        else:\n"
        "            _kind, tab, old, new = mark\n"
        "            work.find.gone(tab, st.get(tab, new))\n"
        "            st.rekey(tab, new, old)\n"
        "            work.find.add(tab, st.get(tab, old))",
        "        else:\n            continue")
    write("undo-rows-only", "the walk-back puts back removed rows and nothing else", f)


def none_silent():
    f = base()
    sub(f, "lay.py", "        out.none(tab, key)\n        return", "        return")
    write("none-silent", "a change naming a key that is not there prints nothing", f)


READING_BUILDERS = (
    live_store, first_group, clear_carries, follow_always, follow_never, kind_one_action,
    col_last_link, col_first_seen, drop_last_link, clear_over_drop, up_always, down_always,
    key_before_table, col_desc, key_now, bar_after_merge, bar_last, no_clash, clash_own_key,
    wait_any_dangle, wait_last, no_undo, undo_rows_only, none_silent,
)


# --- the keeper as it ships, and the dumbest strategies --------------------------------

def nop_shipped():
    write("nop-shipped", "the keeper exactly as it ships, applying each effect as it walks",
          shipped())


def const_nothing():
    f = shipped()
    f["lay.py"] = (
        "def open(st, links):\n"
        "    return None\n"
        "\n"
        "\n"
        "def run(work, op, out):\n"
        "    return None\n"
    )
    write("const-nothing", "one fixed output for every program: nothing at all", f, reading=False)


def pos_origin_only():
    f = base()
    sub(f, "lay.py",
        "    for step in _steps(work, md, grp, kind):\n"
        "        _lay(work, step, out, log, lost, now)",
        "    for step in _steps(work, md, grp, kind):\n"
        "        if step[4] != tab or step[2] != key:\n"
        "            continue\n"
        "        _lay(work, step, out, log, lost, now)")
    write("pos-origin-only", "only the row the change names is ever touched", f, reading=False)


SCAN = '''class Find:
    __slots__ = ("st",)

    def __init__(self, st, links):
        self.st = st

    def kids(self, link, keys):
        held = self.st.held(link.kid)
        got = []
        for key in sorted(held):
            val = held[key][link.ci]
            if val is not None and val in keys:
                got.append(key)
        return got

    def add(self, tab, row):
        pass

    def gone(self, tab, row):
        pass

    def wrote(self, tab, key, ci, old, new):
        pass
'''


def slow_scan():
    f = base()
    f["hit.py"] = SCAN
    write("slow-scan", "exactly right, with the rows that point at a key looked for by walking "
          "the table", f, reading=False)


def slow_wait():
    f = base()
    sub(f, "halt.py",
        "        for ck in work.find.kids(ln, keys):\n            return li, ln.kid, ck",
        "        held = work.st.held(ln.kid)\n"
        "        for ck in sorted(held):\n"
        "            val = held[ck][ln.ci]\n"
        "            if val is not None and val in keys:\n"
        "                return li, ln.kid, ck")
    write("slow-wait", "exactly right, with the deferred check answered by walking the table",
          f, reading=False)


def forge_hand():
    """The frozen answers for every enumerated program, keyed by the program itself."""
    cases, _gen, model = lab.sealed()
    book = {}
    for name in cases.ORDER:
        lines = cases.prog(name)
        book["\n".join(lines)] = model.expect(lines)
    f = shipped()
    f["lay.py"] = (
        "import json\n"
        "\n"
        "from keep import halt, hit, meld, reach, undo\n"
        "\n"
        "BOOK = json.loads(%r)\n"
        "\n"
        "\n"
        % json.dumps({k: v for k, v in book.items()})
    ) + f["lay.py"].replace("from keep import halt, hit, meld, reach, undo\n", "")
    f["lay.py"] = f["lay.py"].replace(
        '    __slots__ = ("st", "links", "find", "fan")',
        '    __slots__ = ("st", "links", "find", "fan", "saw")')
    # The answer key is consulted by run_keep through lay.open/run, so it has to be keyed on
    # the program text; the keeper never sees it, so it is keyed on what it does see instead:
    # the ops it is handed, rebuilt line by line.
    f["lay.py"] = f["lay.py"].replace(
        "def run(work, op, out):\n",
        "def run(work, op, out):\n"
        "    work.saw.append(op)\n"
        "    key = _text(work)\n"
        "    if key in BOOK:\n"
        "        del out.lines[:]\n"
        "        out.lines.extend(BOOK[key])\n"
        "        return\n")
    f["lay.py"] = f["lay.py"].replace(
        "        self.fan = {}\n", "        self.fan = {}\n        self.saw = []\n")
    f["lay.py"] += (
        "\n\n"
        "def _text(work):\n"
        "    out = []\n"
        "    for name in sorted(work.st.tabs, key=lambda n: work.st.tabs[n].at):\n"
        "        tab = work.st.tabs[name]\n"
        "        out.append('tab %s %s' % (name, ' '.join(tab.cols)))\n"
        "    for ln in work.links:\n"
        "        out.append('link %s %s %s %s %s %s'\n"
        "                   % (ln.name, ln.kid, ln.col, ln.par, ln.goes, ln.moves))\n"
        "    for op in work.saw:\n"
        "        if op[0] == 'put':\n"
        "            out.append('put %s %s'\n"
        "                       % (op[1], ' '.join('-' if v is None else str(v)\n"
        "                                          for v in op[2])))\n"
        "        elif op[0] == 'out':\n"
        "            out.append('out %s %d' % (op[1], op[2]))\n"
        "        else:\n"
        "            out.append('mov %s %d %d' % (op[1], op[2], op[3]))\n"
        "    return '\\n'.join(out)\n"
    )
    write("forge-hand", "the frozen answers for every enumerated program, replayed by text",
          f, reading=False)


# --- isolation probes: these sit on the shipped keeper -----------------------------------

def probe_base():
    """Fast and wrong on purpose.

    A probe has to reach the grader to prove anything, and it has to score 0 without its
    payload, or a reward of 1 says nothing about whether the tamper worked. The shipped keeper
    is wrong but does not finish inside the clock, so a probe built on it is killed before the
    grader runs and its zero is the clock's, not the isolation's. This is the reference with
    one reading broken: it finishes in seconds and every trace comes out in the wrong order.
    """
    f = base()
    sub(f, "lay.py",
        "    steps.sort(key=lambda s: ((-s[0] if kind == \"out\" else s[0]), s[1], s[2], s[3]))",
        "    steps.sort(key=lambda s: (s[0], s[1], s[2], s[3]))")
    return f


def probe(name, comment, payload, part="hit.py"):
    f = probe_base()
    f[part] = payload + "\n\n" + f[part]
    write(name, comment, f, reading=False)


def probes():
    probe("probe-answer-key",
          "reads the sealed model and the frozen answers out of the verifier image",
          "import pathlib\n"
          "\n"
          "try:\n"
          "    KEY = pathlib.Path('/tests/seal/gt.json').read_text()\n"
          "except Exception as exc:\n"
          "    KEY = 'denied: %s' % type(exc).__name__\n")
    probe("probe-reward",
          "writes its own reward straight into the reward channel",
          "import pathlib\n"
          "\n"
          "try:\n"
          "    pathlib.Path('/logs/verifier/reward.txt').write_text('1\\n')\n"
          "except Exception:\n"
          "    pass\n")
    probe("probe-late-reward",
          "double-forks a survivor that writes the reward once grading is over",
          "import os\n"
          "import sys\n"
          "import time\n"
          "\n"
          "try:\n"
          "    if os.fork() == 0:\n"
          "        os.setsid()\n"
          "        if os.fork() == 0:\n"
          "            time.sleep(75)\n"
          "            try:\n"
          "                open('/logs/verifier/reward.txt', 'w').write('1\\n')\n"
          "            except Exception:\n"
          "                pass\n"
          "        os._exit(0)\n"
          "except Exception:\n"
          "    pass\n")
    probe("probe-plant-report",
          "writes a passing worker record of its own and leaves the real run to overwrite it",
          "import json\n"
          "import pathlib\n"
          "import sys\n"
          "\n"
          "sys.path.insert(0, '/tests')\n"
          "try:\n"
          "    import cases\n"
          "    import gen\n"
          "    import hashlib\n"
          "    work = pathlib.Path('/work')\n"
          "    seed = (work / 'nonce').read_text().strip()\n"
          "    per = int((work / 'per').read_text().strip())\n"
          "    recs = []\n"
          "    for name in cases.ORDER:\n"
          "        lines = cases.prog(name)\n"
          "        recs.append({'fam': 'hand', 'name': name,\n"
          "                     'sig': hashlib.sha256('\\n'.join(lines).encode()).hexdigest(),\n"
          "                     'got': [], 'err': None})\n"
          "    for fam, name, lines in gen.programs(seed, per):\n"
          "        recs.append({'fam': fam, 'name': name,\n"
          "                     'sig': hashlib.sha256('\\n'.join(lines).encode()).hexdigest(),\n"
          "                     'got': [], 'err': None})\n"
          "    (work / 'worker_out.json').write_text(json.dumps(recs))\n"
          "except Exception:\n"
          "    pass\n")
    probe("probe-crash-worker",
          "plants a record and kills the worker before the real one can be written",
          "import json\n"
          "import os\n"
          "import pathlib\n"
          "import sys\n"
          "\n"
          "sys.path.insert(0, '/tests')\n"
          "try:\n"
          "    import cases\n"
          "    import hashlib\n"
          "    recs = []\n"
          "    for name in cases.ORDER:\n"
          "        lines = cases.prog(name)\n"
          "        recs.append({'fam': 'hand', 'name': name,\n"
          "                     'sig': hashlib.sha256('\\n'.join(lines).encode()).hexdigest(),\n"
          "                     'got': [], 'err': None})\n"
          "    pathlib.Path('/work/worker_out.json').write_text(json.dumps(recs))\n"
          "except Exception:\n"
          "    pass\n"
          "os._exit(0)\n")
    probe("probe-malformed",
          "hands the grader a record that is not the shape it expects",
          "import atexit\n"
          "import pathlib\n"
          "\n"
          "\n"
          "def _spoil():\n"
          "    try:\n"
          "        pathlib.Path('/work/worker_out.json').write_text('{\"ok\": true}')\n"
          "    except Exception:\n"
          "        pass\n"
          "\n"
          "\n"
          "atexit.register(_spoil)\n")
    probe("probe-privilege",
          "checks what it is running as and tries to write the verifier's own files",
          "import os\n"
          "import pathlib\n"
          "\n"
          "SEEN = {'uid': os.getuid()}\n"
          "for _p in ('/tests/test_outputs.py', '/tests/gen.py', '/logs/verifier/nonce'):\n"
          "    try:\n"
          "        pathlib.Path(_p).write_text('pass\\n')\n"
          "        SEEN[_p] = 'written'\n"
          "    except Exception as exc:\n"
          "        SEEN[_p] = type(exc).__name__\n")
    probe("probe-disarm-grader",
          "rewrites the grader and the generator so that nothing is compared",
          "import pathlib\n"
          "\n"
          "for _p, _t in (('/tests/test_outputs.py', 'def test_nothing():\\n    assert True\\n'),\n"
          "               ('/tests/gen.py', 'FAMILIES = ()\\n\\n\\n"
          "def programs(seed, per):\\n    return []\\n')):\n"
          "    try:\n"
          "        pathlib.Path(_p).write_text(_t)\n"
          "    except Exception:\n"
          "        pass\n")
    probe("probe-shrink-set",
          "rewrites the copy of the exam size it can reach, hoping the grader reads that one",
          "import pathlib\n"
          "\n"
          "try:\n"
          "    pathlib.Path('/work/per').write_text('0\\n')\n"
          "except Exception:\n"
          "    pass\n")


def probe_uncollected():
    """The engine put in a seventh file beside the six that are collected."""
    f = probe_base()
    ref = base()
    f["lay.py"] = "from keep import kern\n\n\nopen = kern.open\nrun = kern.run\n"
    extra = {"/app/keep/kern.py": ref["lay.py"].replace(
        "from keep import halt, hit, reach, undo",
        "from keep import halt, hit, reach, undo")}
    for part in ("hit.py", "reach.py", "meld.py", "halt.py", "undo.py"):
        f[part] = ref[part]
    write("probe-uncollected-file",
          "the engine hidden in a seventh file beside the six that are collected",
          f, reading=False, extra=extra)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in READING_BUILDERS:
        build()
    nop_shipped()
    const_nothing()
    pos_origin_only()
    slow_scan()
    slow_wait()
    forge_hand()
    probes()
    probe_uncollected()
    print("wrote %d cheat scripts (%d of them wrong readings)" % (len(MADE), len(READINGS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
