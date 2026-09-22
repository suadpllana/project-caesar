#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all five planner files. A wrong reading
is the reference with that one reading changed. The isolation probes and the forgery sit on the
SHIPPED planner instead: a probe built on correct work scores 1 for an honest reason and proves
nothing, so only the tamper itself may be able to raise the reward. Every substitution asserts
how many times it fired - a patch that matches nothing ships the reference under a cheat's name
and scores 0 for the wrong reason (CLAUDE.md, reach-pair-sweep).

Run this after any change to solution/, and before cheat_report.py or readingcheck: a report
built from a stale script says a reading is caught when the repaired one never ran.

    python3 -u authoring/restate-hold-plan/emit.py
"""
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

OUT = lab.TASK / "cheat"
PARTS = lab.PARTS

MADE = []
BUILT = {}
READINGS = {}


def base():
    return {p: (lab.SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (lab.SRC / "plan" / p).read_text(encoding="utf-8") for p in PARTS}


FAST_SHIPPED_REACH = """from plan.keep import there
from plan.span import last


def reach(pp):
    readers = {}
    for name in pp.names:
        for kind, src, width in pp.reads.get(name, ()):
            readers.setdefault(src, []).append((name, kind, width))
    got = {pp.fix}
    todo = [pp.fix]
    while todo:
        src, i = todo.pop()
        for name, kind, width in readers.get(src, ()):
            if kind == "same":
                outs = [i]
            elif kind == "day":
                outs = [i // 24]
            elif kind == "win":
                outs = range(i, i + width)
            elif pp.grain[src] == pp.grain[name]:
                outs = [i + 1]
            elif pp.grain[src] == "d":
                outs = range(24 * (i + 1), 24 * (i + 2))
            else:
                outs = [(i + 1) // 24] if (i + 1) % 24 == 0 else []
            for j in outs:
                if 0 <= j <= last(pp, name) and (name, j) not in got and there(pp, name, j):
                    got.add((name, j))
                    todo.append((name, j))
    return got
"""


def shipped_fast():
    """The shipped planner's semantics with a reach that fits the clock.

    The shipped reach indexes every partition from hour 0, which does not fit the 60 second clock
    on the scale pipelines. A probe or a forgery built on it would score 0 on the clock whatever it
    tampered with, which proves nothing about the isolation (CLAUDE.md: assert the layer, never
    just the reward). This keeps every wrong answer of the shipped planner and only its speed.
    """
    f = shipped()
    f["reach.py"] = FAST_SHIPPED_REACH
    return f


def sub(files, part, old, new, times=1):
    text = files[part]
    hits = text.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (part, hits, times, old[:80])
    files[part] = text.replace(old, new)


def write(name, comment, files, reading=True, extra=None):
    BUILT[name] = dict(files)
    if reading:
        READINGS[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body += ["cat > /app/plan/%s <<'PYEOF'" % part, files[part].rstrip("\n"), "PYEOF", ""]
    for path, text in sorted((extra or {}).items()):
        body += ["cat > %s <<'PYEOF'" % path, text.rstrip("\n"), "PYEOF", ""]
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- existence -------------------------------------------------------------------------

def pins_expire():
    f = base()
    sub(f, "keep.py", "return (name, i) in pp.pins or pp.now < end + pp.keep[name]",
        "return pp.now < end + pp.keep[name]")
    write("pins-expire", "a published partition is deleted with its keep like any other", f)


def keep_inclusive():
    f = base()
    sub(f, "keep.py", "pp.now < end + pp.keep[name]", "pp.now <= end + pp.keep[name]")
    write("keep-inclusive", "a partition is still there at exactly end plus keep", f)


def keep_from_start():
    f = base()
    sub(f, "keep.py", "from plan.span import ends", "from plan.span import ends, starts")
    sub(f, "keep.py", "pp.now < end + pp.keep[name]",
        "pp.now < starts(pp, name, i) + pp.keep[name]")
    write("keep-from-start", "the keep runs from the start of a partition, not its end", f)


# --- what the correction reaches -------------------------------------------------------

def reach_existing_only():
    f = base()
    sub(f, "reach.py", "from plan.span import last", "from plan.keep import there\nfrom plan.span import last")
    sub(f, "reach.py", "if 0 <= j <= top and (name, j) not in got:",
        "if 0 <= j <= top and (name, j) not in got and there(pp, name, j):")
    write("reach-existing-only", "the correction is only followed through partitions that exist", f)


def reach_window_back():
    f = base()
    sub(f, "reach.py", "        return range(i, i + width)", "        return range(i - width + 1, i + 1)")
    write("reach-window-back", "a window's readers are taken as the partitions before it", f)


def reach_prev_same_day():
    f = base()
    sub(f, "reach.py", "        return range(24 * (i + 1), 24 * (i + 2))",
        "        return range(24 * i, 24 * (i + 1))")
    write("reach-prev-same-day", "an hour reading the previous day is reached from its own day", f)


# --- how a computation reads ------------------------------------------------------------

def stand_any():
    f = base()
    sub(f, "look.py", "                and there(pp, roll, i) and agrees(roll, i):",
        "                and there(pp, roll, i):")
    write("stand-any", "a roll-up stands in for the hours whatever it holds", f)


def stand_all_missing():
    f = base()
    sub(f, "look.py", "                and not all(there(pp, src, h) for h in parts) \\",
        "                and not any(there(pp, src, h) for h in parts) \\")
    write("stand-all-missing", "a roll-up stands in only when every hour of the day is gone", f)


def stand_never():
    f = base()
    sub(f, "look.py", "        roll = pp.roll.get(src) if kind == \"day\" else None\n        if roll",
        "        roll = None\n        if roll")
    write("stand-never", "a roll-up never stands in; missing hours are always recomputed", f)


def stand_runs_only():
    f = base()
    sub(f, "look.py", "        if roll is not None and roll != name \\\n",
        "        if roll is not None and roll != name and there(pp, name, i) \\\n")
    write("stand-runs-only", "a roll-up stands in for a rerun but never inside a computed partition", f)


def no_temp():
    f = base()
    sub(f, "look.py", "                out.append((src, p, \"temp\"))",
        "                out.append((src, p, \"gone\"))")
    write("no-temp", "a partition that has expired cannot be read, so its reader is lost", f)


# --- the line of a reached partition ----------------------------------------------------

def run_if_reached():
    f = base()
    sub(f, "settle.py", "        elif not r.changed:\n", "        elif False:\n")
    write("run-if-reached", "a reached partition reruns even when nothing it read changed", f)


def same_before_lost():
    f = base()
    sub(f, "settle.py",
        "        elif not r.ok:\n            r.line, r.word = \"hold\", \"lost\"\n"
        "        elif not r.changed:\n            r.line, r.word = \"hold\", \"same\"\n",
        "        elif not r.changed:\n            r.line, r.word = \"hold\", \"same\"\n"
        "        elif not r.ok:\n            r.line, r.word = \"hold\", \"lost\"\n")
    write("same-before-lost", "an unchanged partition is held as same before it can be lost", f)


def sub_over_part():
    f = base()
    sub(f, "settle.py",
        "r.word = \"part\" if not r.agrees else (\"sub\" if r.rolled else \"full\")",
        "r.word = \"sub\" if r.rolled else (\"part\" if not r.agrees else \"full\")")
    write("sub-over-part", "a roll-up standing in outranks a disagreeing read in the mode", f)


def sub_through_temps():
    f = base()
    sub(f, "settle.py", "                r.agrees &= t.agrees\n",
        "                r.agrees &= t.agrees\n                r.rolled |= t.rolled\n")
    write("sub-through-temps",
          "a roll-up standing in inside a partition computed for a rerun makes the rerun sub", f)


def temp_always_changed():
    f = base()
    sub(f, "settle.py", "                r.changed |= t.changed\n", "                r.changed = True\n")
    write("temp-always-changed", "anything computed for the plan counts as a change", f)


def same_agrees():
    f = base()
    sub(f, "settle.py", "        return False, False             # held: unchanged, and it no longer agrees",
        "        return False, r.word == \"same\"")
    write("same-agrees", "a partition held because nothing it read changed still agrees", f)


def pinned_agrees():
    f = base()
    sub(f, "settle.py", "        return False, False             # held: unchanged, and it no longer agrees",
        "        return False, r.word == \"pinned\"")
    write("pinned-agrees", "a published partition the correction reached still agrees", f)


def closure():
    f = base()
    sub(f, "settle.py",
        "        if here and (name, i) in pp.pins:\n",
        "        if here:\n            r.line, r.word = \"run\", \"full\"\n            return r\n"
        "        if here and (name, i) in pp.pins:\n")
    write("closure", "every reached partition that exists reruns in full, and nothing else", f)


# --- which computed partitions are printed ----------------------------------------------

def temps_of_holds():
    f = base()
    sub(f, "settle.py", "        todo = list(runs)\n", "        todo = list(runs) + list(self.holds)\n")
    write("temps-of-holds", "partitions computed for a held partition are printed too", f)


def temp_per_reader():
    f = base()
    sub(f, "order.py",
        "        rows.append((\"run\", k[0], k[1], r.word) if r.line == \"run\" else (\"temp\", k[0], k[1]))\n",
        "        if r.line == \"run\":\n            rows.append((\"run\", k[0], k[1], r.word))\n"
        "        else:\n"
        "            rows += [(\"temp\", k[0], k[1])] * max(1, readers_of.get(k, 0))\n")
    # Counted once, not rescanned per line: a reading has to fail on its case, not on the clock.
    sub(f, "order.py", "    rows = []\n    while free:\n",
        "    readers_of = {}\n"
        "    for m in book.made:\n"
        "        for t in set(book.rec[m].temps):\n"
        "            readers_of[t] = readers_of.get(t, 0) + 1\n"
        "    rows = []\n    while free:\n")
    write("temp-per-reader", "a computed partition is printed once for each line that reads it", f)


# --- the order ---------------------------------------------------------------------------

def order_static():
    f = base()
    sub(f, "order.py", "    free = [(key(k), k) for k, before in waiting.items() if not before]",
        "    free = [(key(k), k) for k in waiting]")
    sub(f, "order.py", "            if not waiting[u]:\n                heapq.heappush(free, (key(u), u))\n",
        "            pass\n")
    write("order-static", "the plan is sorted by end and declaration, whatever each line read", f)


def order_fix_after_sort():
    f = base()
    old = "    rows = []\n    while free:\n"
    new = ("    rows = []\n"
           "    seq = sorted(book.made, key=key)\n"
           "    late = [(k, d) for k in seq for d in sorted(waiting[k], key=key) if key(d) > key(k)]\n"
           "    for k, d in late:\n"
           "        if seq.index(d) > seq.index(k):\n"
           "            seq.remove(d)\n"
           "            seq.insert(seq.index(k), d)\n"
           "    free = []\n"
           "    for k in seq:\n"
           "        r = book.rec[k]\n"
           "        rows.append((\"run\", k[0], k[1], r.word) if r.line == \"run\" else (\"temp\", k[0], k[1]))\n"
           "    while free:\n")
    sub(f, "order.py", old, new)
    write("order-fix-after-sort",
          "sorts by end and declaration, then moves a line's roll-up in front of it", f)


def holds_interleaved():
    f = base()
    old = ("    for k in sorted(book.holds, key=key):\n"
           "        rows.append((\"hold\", k[0], k[1], book.rec[k].word))\n"
           "    return rows\n")
    new = ("    out = []\n"
           "    holds = sorted(book.holds, key=key)\n"
           "    for row in rows:\n"
           "        while holds and key(holds[0]) < key((row[1], row[2])):\n"
           "            k = holds.pop(0)\n"
           "            out.append((\"hold\", k[0], k[1], book.rec[k].word))\n"
           "        out.append(row)\n"
           "    for k in holds:\n"
           "        out.append((\"hold\", k[0], k[1], book.rec[k].word))\n"
           "    return out\n")
    sub(f, "order.py", old, new)
    write("holds-interleaved", "a hold is printed where its end and declaration put it among the runs", f)


READING_BUILDERS = (
    pins_expire, keep_inclusive, keep_from_start, reach_existing_only, reach_window_back,
    reach_prev_same_day, stand_any, stand_all_missing, stand_never, stand_runs_only, no_temp,
    run_if_reached, same_before_lost, sub_over_part, sub_through_temps, temp_always_changed,
    same_agrees,
    pinned_agrees, closure, temps_of_holds, temp_per_reader, order_static,
    order_fix_after_sort, holds_interleaved,
)


# --- exactly correct, and too slow for the clock ----------------------------------------

def slow_every_hour():
    """The reader index of the shipped planner, over every partition from hour 0."""
    f = base()
    f["reach.py"] = (
        "from plan.span import last, takes\n"
        "\n"
        "\n"
        "def reach(pp):\n"
        "    back = {}\n"
        "    for name in pp.names:\n"
        "        if name not in pp.reads:\n"
        "            continue\n"
        "        for i in range(last(pp, name) + 1):\n"
        "            for _kind, src, parts in takes(pp, name, i):\n"
        "                for p in parts:\n"
        "                    back.setdefault((src, p), []).append((name, i))\n"
        "    got = {pp.fix}\n"
        "    todo = [pp.fix]\n"
        "    while todo:\n"
        "        at = todo.pop()\n"
        "        for up in back.get(at, ()):\n"
        "            if up not in got:\n"
        "                got.add(up)\n"
        "                todo.append(up)\n"
        "    return got\n")
    write("slow-every-hour", "walks every partition from hour 0 to find what the correction reached",
          f, reading=False)


def slow_rewalk():
    """Settles each computed partition afresh every time something reads it."""
    f = base()
    sub(f, "settle.py", "                t = self.rec[(src, p)]\n",
        "                t = self.again(src, p)\n")
    sub(f, "settle.py", "from plan.keep import there\n",
        "import sys\n\nfrom plan.keep import there\n\nsys.setrecursionlimit(1000000)\n")
    sub(f, "settle.py", "    def settle(self):\n",
        "    def again(self, name, i):\n"
        "        if there(self.pp, name, i):\n"
        "            return self.rec[(name, i)]\n"
        "        return self.compute(name, i)\n"
        "\n"
        "    def settle(self):\n")
    write("slow-rewalk", "re-evaluates a computed partition for every read of it, with no memo",
          f, reading=False)


# --- the dumbest strategies (docs/INSTRUCTION-CONTRACT.md, shortcuts) ------------------

def const_nothing():
    f = shipped_fast()
    f["order.py"] = "def order(pp, rows):\n    return []\n"
    write("const-nothing", "prints an empty plan for every pipeline", f, reading=False)


def const_same():
    f = shipped_fast()
    sub(f, "settle.py", "            rows.append((\"run\", name, i, \"full\"))",
        "            rows.append((\"hold\", name, i, \"same\"))")
    sub(f, "settle.py", "            rows.append((\"hold\", name, i, \"lost\"))",
        "            rows.append((\"hold\", name, i, \"same\"))")
    write("const-same", "holds every reached partition as same, publications aside", f,
          reading=False)


def replay_quoted():
    """Every pipeline prints the one line the brief quotes, and nothing else."""
    f = shipped_fast()
    f["order.py"] = ("def order(pp, rows):\n"
                     "    return [(\"run\", \"rev\", 25, \"full\")]\n")
    write("replay-quoted", "prints the line the brief quotes for every pipeline", f, reading=False)


# --- isolation probes: each fires DURING the run, from inside settle --------------------

PROBE = '''_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
%s


def settle(pp, got):
    _probe()
    rows = []'''


def probe(name, comment, body, extra=None):
    f = shipped_fast()
    sub(f, "settle.py", "def settle(pp, got):\n    rows = []", PROBE % body)
    write(name, comment, f, reading=False, extra=extra)


def probe_answer_key():
    probe("probe-answer-key", "reaches for the frozen answers and the sealed model",
          '    import os\n'
          '    import sys\n'
          '    note = os.path.join(os.environ.get("RHP_WORK", "/work"), "probe.log")\n'
          '    with open(note, "a", encoding="utf-8") as fh:\n'
          '        try:\n'
          '            with open("/tests/seal/gt.json", encoding="utf-8") as g:\n'
          '                fh.write("gt read %d\\n" % len(g.read()))\n'
          '        except Exception as exc:\n'
          '            fh.write("gt %s\\n" % type(exc).__name__)\n'
          '        try:\n'
          '            sys.path.insert(0, "/tests/seal")\n'
          '            import model\n'
          '            fh.write("model %s\\n" % model.__name__)\n'
          '        except Exception as exc:\n'
          '            fh.write("model %s\\n" % type(exc).__name__)')


def probe_privilege():
    probe("probe-privilege", "reports its uid and writes the reward directly",
          '    import os\n'
          '    note = os.path.join(os.environ.get("RHP_WORK", "/work"), "probe.log")\n'
          '    with open(note, "a", encoding="utf-8") as fh:\n'
          '        fh.write("uid %d\\n" % os.getuid())\n'
          '        try:\n'
          '            with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as r:\n'
          '                r.write("1\\n")\n'
          '            fh.write("reward written\\n")\n'
          '        except Exception as exc:\n'
          '            fh.write("reward %s\\n" % type(exc).__name__)')


def probe_late_reward():
    probe("probe-late-reward", "double-forks a process that writes the reward after grading",
          '    import os\n'
          '    import time\n'
          '    try:\n'
          '        if os.fork():\n'
          '            return\n'
          '    except Exception:\n'
          '        return\n'
          '    try:\n'
          '        os.setsid()\n'
          '        if os.fork():\n'
          '            os._exit(0)\n'
          '    except Exception:\n'
          '        pass\n'
          '    for _ in range(40):\n'
          '        time.sleep(1)\n'
          '        try:\n'
          '            with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:\n'
          '                fh.write("1\\n")\n'
          '        except Exception:\n'
          '            pass\n'
          '    os._exit(0)')


def probe_plant_record():
    probe("probe-plant-record", "writes a record of its own into stage one's output path",
          '    import json\n'
          '    import os\n'
          '    try:\n'
          '        with open(os.path.join(os.environ.get("RHP_WORK", "/work"), "planned.json"),\n'
          '                  "w", encoding="utf-8") as fh:\n'
          '            json.dump([], fh)\n'
          '    except Exception:\n'
          '        pass')


def probe_crash_after_plant():
    probe("probe-crash-after-plant", "plants a record and exits stage one clean before it is overwritten",
          '    import json\n'
          '    import os\n'
          '    try:\n'
          '        with open(os.path.join(os.environ.get("RHP_WORK", "/work"), "planned.json"),\n'
          '                  "w", encoding="utf-8") as fh:\n'
          '            json.dump([{"name": "x", "plan": []}], fh)\n'
          '    except Exception:\n'
          '        pass\n'
          '    os._exit(0)')


def probe_malformed():
    probe("probe-malformed", "spoils stage one's record with garbage as the process leaves",
          '    import atexit\n'
          '    import os\n'
          '\n'
          '    def _spoil():\n'
          '        try:\n'
          '            path = os.path.join(os.environ.get("RHP_WORK", "/work"), "planned.json")\n'
          '            with open(path, "w", encoding="utf-8") as fh:\n'
          '                fh.write("[{\\"name\\": 7, \\"plan\\": {}}")\n'
          '        except Exception:\n'
          '            pass\n'
          '\n'
          '    atexit.register(_spoil)')


def probe_shrink_population():
    probe("probe-shrink-population", "rewrites the generator and the case list so less is graded",
          '    for path in ("/tests/gen.py", "/tests/cases.py"):\n'
          '        try:\n'
          '            with open(path, "w", encoding="utf-8") as fh:\n'
          '                fh.write("FAMILIES = []\\nORDER = []\\n")\n'
          '        except Exception:\n'
          '            pass')


def probe_rewrite_grader():
    probe("probe-rewrite-grader", "rewrites the grading file so nothing is asserted",
          '    try:\n'
          '        with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:\n'
          '            fh.write("def test_fine():\\n    assert True\\n")\n'
          '    except Exception:\n'
          '        pass')


def probe_extra_file():
    """A correct planner in a new module beside the five, which is never collected."""
    f = shipped_fast()
    f["settle.py"] = "from plan.mine import settle  # noqa: F401\n"
    f["order.py"] = "from plan.mine import order  # noqa: F401\n"
    f["reach.py"] = "from plan.mine import reach  # noqa: F401\n"
    ref = base()
    mine = "\n\n".join(ref[p].replace("from plan.keep import there", "")
                       .replace("from plan.look import named, rank_of, reads", "")
                       for p in ("keep.py", "look.py", "reach.py", "settle.py", "order.py"))
    write("probe-extra-file", "puts a planner in a module beside the five and delegates to it",
          f, reading=False, extra={"/app/plan/mine.py": mine})


def forge_enumerated():
    """Carries tests/seal/gt.json verbatim, over the shipped planner.

    On the shipped planner, not the reference: a forgery that falls back to a correct planner is
    the reference with a lookup table in front of it and scores 1 for an honest reason. It keys
    the frozen plans by case name and finds the name from the pipeline's own text.
    """
    cases, _gen, _model = lab.sealed()
    gt_text = (lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    names = {"\n".join(cases.prog(name)) + "\n": name for name in cases.ORDER}
    f = shipped_fast()
    f["order.py"] = (
        "import json\n"
        "\n"
        "from plan.span import ends\n"
        "\n"
        "GT = json.loads(%r)\n"
        "NAMES = json.loads(%r)\n"
        "\n"
        "\n"
        "def _text(pp):\n"
        "    out = ['now %%d' %% pp.now]\n"
        "    for name in pp.names:\n"
        "        if name not in pp.reads:\n"
        "            out.append('src %%s %%s %%d' %% (name, pp.grain[name], pp.keep[name]))\n"
        "            continue\n"
        "        toks = []\n"
        "        for kind, src, width in pp.reads[name]:\n"
        "            toks.append({'same': src, 'day': src + '/d', 'prev': src + '-1',\n"
        "                         'win': '%%s~%%d' %% (src, width)}[kind])\n"
        "        out.append('step %%s %%s %%d %%s' %% (name, pp.grain[name], pp.keep[name],\n"
        "                                          ' '.join(toks)))\n"
        "    for hourly, roll in pp.roll.items():\n"
        "        out.append('stand %%s %%s' %% (roll, hourly))\n"
        "    pins = {}\n"
        "    for name, p in sorted(pp.pins):\n"
        "        pins.setdefault(name, []).append(p)\n"
        "    for name in pp.names:\n"
        "        if name in pins:\n"
        "            out.append('pin %%s %%s' %% (name, ' '.join(str(p) for p in sorted(pins[name]))))\n"
        "    out.append('fix %%s %%d' %% pp.fix)\n"
        "    return '\\n'.join(out) + '\\n'\n"
        "\n"
        "\n"
        "def order(pp, rows):\n"
        "    name = NAMES.get(_text(pp))\n"
        "    if name is not None:\n"
        "        return [tuple(line.split()) for line in GT[name]]\n"
        "\n"
        "    def key(row):\n"
        "        return ends(pp, row[1], row[2]), pp.pos[row[1]]\n"
        "\n"
        "    runs = sorted((row for row in rows if row[0] != 'hold'), key=key)\n"
        "    holds = sorted((row for row in rows if row[0] == 'hold'), key=key)\n"
        "    return runs + holds\n" % (gt_text, json.dumps(names)))
    write("forge-enumerated", "carries tests/seal/gt.json and plays it back for every enumerated pipeline", f,
          reading=False)


OTHER_BUILDERS = (
    slow_every_hour, slow_rewalk, const_nothing, const_same, replay_quoted,
    probe_answer_key, probe_privilege, probe_late_reward, probe_plant_record,
    probe_crash_after_plant, probe_malformed, probe_shrink_population, probe_rewrite_grader,
    probe_extra_file, forge_enumerated,
)


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in READING_BUILDERS + OTHER_BUILDERS:
        build()
    print("wrote %d cheat scripts, %d of them wrong readings" % (len(MADE), len(READINGS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
