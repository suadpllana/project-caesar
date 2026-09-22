#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed. The isolation probes and the forgery sit on the
reference with a named wrong reading already in it: correct work scores 1 for an honest reason
and proves nothing, and the shipped service does not finish inside the execution limit, so its
0 would come from the clock and prove nothing either. Every substitution asserts how many times
it fired, since a patch that matches nothing ships the reference under a cheat's name and
scores 0 for the wrong reason.

Run this after any change to solution/, and before cheat_report.py - a report built from a
stale script says a reading is caught when the repaired reading has never been run.

    python3 -u authoring/feed-lag-pare/emit.py
"""
import hashlib
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


def bare(text):
    """The reference file without its leading docstring.

    A cheat script ships in the bundle, and the reference's module docstrings describe the
    method it is supposed to be getting wrong. Stripping them also keeps every cheat file
    byte-stable when the reference gains or loses a comment, so a prose change does not
    invalidate a cheat suite that has already been run through the containers.
    """
    if not text.startswith('"""'):
        return text
    end = text.index('"""', 3) + 3
    return text[end:].lstrip("\n")


def base():
    return {p: bare((SOL / p).read_text(encoding="utf-8")) for p in PARTS}


def shipped():
    return {p: (lab.SRC / "lg" / p).read_text(encoding="utf-8") for p in PARTS}


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
        body.append("cat > /app/lg/%s <<'PYEOF'" % part)
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


# --- the fold ---------------------------------------------------------------------------

def fold_add_noop():
    f = base()
    sub(f, "fold.py", '        return arg if cur is ABSENT else cur + arg',
        '        return cur if cur is ABSENT else cur + arg')
    write("fold-add-noop", "an add onto an absent key leaves it absent", f)


def fold_del_is_zero():
    f = base()
    sub(f, "fold.py", '    return ABSENT\n\n\ndef same', '    return 0\n\n\ndef same')
    write("fold-del-zero", "a delete makes the value zero rather than absent", f)


# --- held points and the trailing point --------------------------------------------------

def head_not_held():
    f = base()
    sub(f, "pin.py", "        pts = {self.st.head}", "        pts = set()")
    write("head-not-held", "the head does not count as a held point", f)


def trailing_ignores_range():
    f = base()
    sub(f, "pin.py",
        "        for point, lo, hi in self.fd.values():\n"
        "            if lo <= key <= hi and (best is None or point < best):\n"
        "                best = point",
        "        for point, _lo, _hi in self.fd.values():\n"
        "            if best is None or point < best:\n"
        "                best = point")
    write("trailing-any-feed", "the trailing point is taken over every feed, covering or not", f)


def held_ignores_range():
    f = base()
    sub(f, "pin.py",
        "        for point, lo, hi in self.fd.values():\n"
        "            if lo <= key <= hi:\n                pts.add(point)",
        "        for point, _lo, _hi in self.fd.values():\n            pts.add(point)")
    write("held-any-feed", "every feed's position is a held point of every key", f)


def trailing_takes_highest():
    f = base()
    sub(f, "pin.py", "            if lo <= key <= hi and (best is None or point < best):",
        "            if lo <= key <= hi and (best is None or point > best):")
    write("trailing-highest", "the trailing point is the highest feed position, not the lowest", f)


def unmark_takes_the_point():
    f = base()
    sub(f, "pin.py",
        "    def unmark(self, name):\n        del self.mk[name]\n        self.st.soil_all()",
        "    def unmark(self, name):\n        gone = self.mk.pop(name)\n"
        "        for other in [n for n, at in self.mk.items() if at == gone]:\n"
        "            del self.mk[other]\n        self.st.soil_all()")
    write("unmark-frees-point", "removing one mark frees the point for every mark on it", f)


def close_leaves_stale():
    f = base()
    sub(f, "pin.py",
        "    def close(self, name):\n        rec = self.fd.pop(name)\n"
        "        self.st.soil(rec[1], rec[2])",
        "    def close(self, name):\n        del self.fd[name]")
    write("close-leaves-stale", "closing a feed does not put its keys back in play", f)


def unmark_leaves_stale():
    f = base()
    sub(f, "pin.py",
        "    def unmark(self, name):\n        del self.mk[name]\n        self.st.soil_all()",
        "    def unmark(self, name):\n        del self.mk[name]")
    write("unmark-leaves-stale", "removing a mark does not merge the spans it separated", f)


# --- acknowledgements --------------------------------------------------------------------

def ack_any_point():
    f = base()
    sub(f, "pin.py", "        if seq > rec[0] and seq <= self.st.head:",
        "        if True:")
    write("ack-any-point", "an acknowledgement moves the feed wherever it names", f)


def ack_past_head():
    f = base()
    sub(f, "pin.py", "        if seq > rec[0] and seq <= self.st.head:", "        if seq > rec[0]:")
    write("ack-past-head", "an acknowledgement may carry a feed past the head", f)


# --- the span cut ------------------------------------------------------------------------

def span_to_head():
    f = base()
    sub(f, "span.py", "    top = pins.trailing(key)", "    top = store.head")
    write("span-to-head", "spans are cut to the head, so a feed keeps nothing back", f)


def span_always_keeps():
    f = base()
    sub(f, "span.py", "        won = count - (0 if fold.same(lo, hi) else 1)",
        "        won = count - 1")
    sub(f, "span.py", "    keep = None if fold.same(lo, hi) else last", "    keep = last")
    write("span-always-keeps", "a span holding entries always keeps one of them", f)


def span_keeps_first():
    f = base()
    sub(f, "span.py",
        "            last = seqs[at]\n            count += 1",
        "            last = seqs[at] if last is None else last\n            count += 1")
    write("span-keeps-first", "the entry left behind is the first of the span, not the last", f)


def span_written_last():
    f = base()
    sub(f, "store.py",
        "        self.idx.setdefault(key, []).append(self.head)\n        self.live += 1",
        "        self.idx.setdefault(key, []).append(self.head)\n"
        "        self.ever.setdefault(key, []).append(self.head)\n        self.live += 1")
    sub(f, "store.py", "        self.idx = {}\n        self.head = 0",
        "        self.idx = {}\n        self.ever = {}\n        self.head = 0")
    sub(f, "store.py",
        "    def keys(self):\n        return sorted(self.idx)",
        "    def written(self, key, floor, top):\n        row = self.ever.get(key, [])\n"
        "        cut = [s for s in row if floor < s <= top]\n        return cut[-1] if cut else None\n"
        "\n    def keys(self):\n        return sorted(self.idx)")
    sub(f, "span.py",
        "        if count:\n            out.append((floor, edge, count, last, lo, cur))",
        "        if count:\n"
        "            out.append((floor, edge, count, store.written(key, floor, edge), lo, cur))")
    write("span-written-last",
          "the entry left behind sits where the program wrote last, not where the log holds last",
          f)


def span_del_as_zero():
    f = base()
    sub(f, "span.py",
        "        if hi is fold.ABSENT:\n            store.put(keep, \"del\", key, None)\n"
        "        else:\n            store.put(keep, \"set\", key, hi)",
        "        store.put(keep, \"set\", key, 0 if hi is fold.ABSENT else hi)")
    write("span-del-as-zero", "an absent key is left behind as a set of zero", f)


def span_floor_included():
    f = base()
    sub(f, "store.py",
        "        return row[bisect.bisect_right(row, floor):bisect.bisect_right(row, top)]",
        "        return row[bisect.bisect_left(row, floor):bisect.bisect_right(row, top)]")
    write("span-floor-included", "a span takes in the entry standing on its floor", f)


# --- the budgeted pare -------------------------------------------------------------------

def pare_key_order():
    f = base()
    sub(f, "pare.py",
        "        won, edge, key, floor, last, lo, hi, mark = heap[0]\n        heapq.heappop(heap)",
        "        won, edge, key, floor, last, lo, hi, mark = min(\n"
        "            heap, key=lambda row: (row[2], row[1]))\n        heap.remove(\n"
        "            (won, edge, key, floor, last, lo, hi, mark))")
    write("pare-key-order", "pairs are collapsed in key order rather than by what they remove", f)


def pare_tie_higher_span():
    f = base()
    sub(f, "span.py",
        "            heapq.heappush(store.heap, (-won, edge, key, floor, last, lo, hi, mark))",
        "            heapq.heappush(store.heap, (-won, -edge, key, floor, last, lo, hi, mark))")
    sub(f, "pare.py", "        won, edge, key, floor, last, lo, hi, mark = heap[0]",
        "        won, negedge, key, floor, last, lo, hi, mark = heap[0]\n        edge = -negedge")
    write("pare-tie-higher", "equal removals go to the span with the higher top", f)


def pare_tie_larger_key():
    f = base()
    sub(f, "span.py",
        "            heapq.heappush(store.heap, (-won, edge, key, floor, last, lo, hi, mark))",
        "            heapq.heappush(store.heap, (-won, edge, -key, floor, last, lo, hi, mark))")
    sub(f, "pare.py", "        won, edge, key, floor, last, lo, hi, mark = heap[0]",
        "        won, edge, negkey, floor, last, lo, hi, mark = heap[0]\n        key = -negkey")
    write("pare-tie-larger-key", "equal removals at one span top go to the larger key", f)


def pare_one_under():
    f = base()
    sub(f, "pare.py", "    if store.count() <= budget:\n        return gone",
        "    if store.count() < budget:\n        return gone")
    sub(f, "pare.py", "    while heap and store.count() > budget:",
        "    while heap and store.count() >= budget:")
    write("pare-one-under", "a pare runs until the log is under the budget, not at it", f)


def pare_count_is_head():
    f = base()
    sub(f, "store.py", "    def count(self):\n        return self.live",
        "    def count(self):\n        return self.head")
    write("pare-count-head", "the budget is compared against every entry ever appended", f)


# --- the report --------------------------------------------------------------------------

def tell_first_touch():
    f = base()
    sub(f, "tell.py", "    for key in sorted(rows):", "    for key in rows:")
    write("tell-first-touch", "the report lists keys in the order they were first written", f)


def tell_absent_zero():
    f = base()
    sub(f, "tell.py", '    return "-" if val is fold.ABSENT else str(val)',
        '    return "0" if val is fold.ABSENT else str(val)')
    write("tell-absent-zero", "an absent key reads back as zero", f)


READING_BUILDERS = (
    fold_add_noop, fold_del_is_zero, head_not_held, trailing_ignores_range,
    held_ignores_range, trailing_takes_highest, unmark_takes_the_point, close_leaves_stale,
    unmark_leaves_stale, ack_any_point, ack_past_head, span_to_head, span_always_keeps,
    span_keeps_first, span_written_last, span_del_as_zero, span_floor_included,
    pare_key_order, pare_tie_higher_span, pare_tie_larger_key, pare_one_under,
    pare_count_is_head, tell_first_touch, tell_absent_zero,
)


# --- correct, and too slow ----------------------------------------------------------------

def slow_rebuild():
    """The span table rebuilt for every key on every pare."""
    f = base()
    sub(f, "span.py",
        "def settle(store, pins):\n    for key in list(store.dirty):",
        "def settle(store, pins):\n    store.dirty.update(store.idx)\n"
        "    store.tab.clear()\n    for key in list(store.dirty):")
    write("slow-rebuild", "correct, but every key's spans are rebuilt on every pare", f,
          reading=False)


def slow_repick():
    """The pair table re-formed after every single collapse."""
    f = base()
    sub(f, "pare.py",
        "        gone += span.collapse(store, key, floor, edge, last, lo, hi)\n    return gone",
        "        gone += span.collapse(store, key, floor, edge, last, lo, hi)\n"
        "        store.heap = []\n        store.tab.clear()\n"
        "        store.dirty.update(store.idx)\n        span.settle(store, pins)\n"
        "        heap = store.heap\n    return gone")
    write("slow-repick", "correct, but the pair table is re-formed after every collapse", f,
          reading=False)


# --- shortcut strategies -------------------------------------------------------------------

def keep_everything():
    f = base()
    f["pare.py"] = "def run(store, pins, budget):\n    return 0\n"
    write("pos-keep-all", "a pare that never removes anything", f, reading=False)


def const_one_line():
    f = base()
    f["pare.py"] = "def run(store, pins, budget):\n    return 0\n"
    f["tell.py"] = (
        "def shown(val):\n"
        "    return \"0\"\n"
        "\n"
        "\n"
        "def report(store):\n"
        "    return [\"log 1\", \"k 0 1s1\"]\n"
    )
    write("const-one-line", "one fixed output for every program", f, reading=False)


def replay_example():
    f = base()
    f["pare.py"] = "def run(store, pins, budget):\n    return 2\n"
    f["tell.py"] = (
        "def shown(val):\n"
        "    return \"7\"\n"
        "\n"
        "\n"
        "def report(store):\n"
        "    return [\"log 2\", \"k 0 1s4 2a3\"]\n"
    )
    write("replay-example", "the worked example's lines replayed for every program", f,
          reading=False)


# --- isolation probes ----------------------------------------------------------------------
#
# Every one of these has to interfere DURING the run: a probe wired to import time fires
# before the runner has armed anything and proves nothing. They are hung on Store.__init__,
# which the driver calls once per program, inside the worker's loop.

PROBE_HEAD = """_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
%s


"""


def probe(name, comment, body, extra=None):
    # The reference with one named wrong reading in it, never correct work and never the
    # shipped service. Correct work scores 1 for an honest reason and proves nothing about
    # the isolation; the shipped service does not finish inside the execution limit, so its
    # 0 would come from the clock and prove nothing either. This way the trace is wrong, the
    # run is quick, and the only thing that can raise the reward is the tamper.
    f = base()
    sub(f, "tell.py", '    return "-" if val is fold.ABSENT else str(val)',
        '    return "0" if val is fold.ABSENT else str(val)')
    sub(f, "store.py", "class Store:\n    def __init__(self):",
        (PROBE_HEAD % body) + "class Store:\n    def __init__(self):\n        _probe()")
    write(name, comment, f, reading=False, extra=extra)


def probe_answer_key():
    probe("probe-answer-key",
          "reaches for the sealed model and the frozen answers",
          '    import sys\n'
          '    try:\n'
          '        with open("/tests/seal/gt.json", encoding="utf-8") as fh:\n'
          '            print("gt %d" % len(fh.read()))\n'
          '    except Exception as exc:\n'
          '        print("gt %s" % type(exc).__name__)\n'
          '    try:\n'
          '        sys.path.insert(0, "/tests/seal")\n'
          '        import model\n'
          '        print("model %s" % model.__name__)\n'
          '    except Exception as exc:\n'
          '        print("model %s" % type(exc).__name__)')


def probe_privilege():
    probe("probe-privilege",
          "checks its uid and writes at the reward directly",
          '    import os\n'
          '    print("uid %d" % os.getuid())\n'
          '    try:\n'
          '        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:\n'
          '            fh.write("1\\n")\n'
          '        print("reward written")\n'
          '    except Exception as exc:\n'
          '        print("reward %s" % type(exc).__name__)')


def probe_late_reward():
    probe("probe-late-reward",
          "double-forks a process that writes the reward after grading",
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
          '    time.sleep(25)\n'
          '    try:\n'
          '        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:\n'
          '            fh.write("1\\n")\n'
          '    except Exception:\n'
          '        pass\n'
          '    os._exit(0)')


def probe_plant_report():
    probe("probe-plant-report",
          "writes a passing worker record and lets the worker carry on",
          '    import json\n'
          '    import os\n'
          '    try:\n'
          '        path = os.environ.get("FLP_WORK", "/work") + "/worker_out.json"\n'
          '        with open(path, "w", encoding="utf-8") as fh:\n'
          '            json.dump([], fh)\n'
          '        print("planted")\n'
          '    except Exception as exc:\n'
          '        print("plant %s" % type(exc).__name__)')


def probe_crash_worker():
    probe("probe-crash-worker",
          "plants a record and exits the worker clean before it can be overwritten",
          '    import json\n'
          '    import os\n'
          '    try:\n'
          '        path = os.environ.get("FLP_WORK", "/work") + "/worker_out.json"\n'
          '        with open(path, "w", encoding="utf-8") as fh:\n'
          '            json.dump([], fh)\n'
          '    except Exception:\n'
          '        pass\n'
          '    os._exit(0)')


def probe_malformed():
    probe("probe-malformed",
          "overwrites the worker record with garbage as the process leaves",
          '    import atexit\n'
          '    import os\n'
          '\n'
          '    def _spoil():\n'
          '        try:\n'
          '            path = os.environ.get("FLP_WORK", "/work") + "/worker_out.json"\n'
          '            with open(path, "w", encoding="utf-8") as fh:\n'
          '                fh.write("{not json at all")\n'
          '        except Exception:\n'
          '            pass\n'
          '\n'
          '    atexit.register(_spoil)')


def probe_shrink_set():
    probe("probe-shrink-set",
          "rewrites the generator so the population it is graded on is smaller",
          '    for path in ("/tests/gen.py", "/tests/cases.py"):\n'
          '        try:\n'
          '            with open(path, "w", encoding="utf-8") as fh:\n'
          '                fh.write("FAMILIES = ()\\nORDER = []\\n")\n'
          '            print("rewrote %s" % path)\n'
          '        except Exception as exc:\n'
          '            print("%s %s" % (path, type(exc).__name__))')


def probe_uncollected_file():
    """A correct span module in a new file under /app/lg, which is not one of the six."""
    f = shipped()
    f["span.py"] = ("from lg import own\n\n\n"
                    "def build(store, pins, key):\n    return own.build(store, pins, key)\n\n\n"
                    "def freshen(store, pins, key):\n    return own.freshen(store, pins, key)\n\n\n"
                    "def settle(store, pins):\n    return own.settle(store, pins)\n\n\n"
                    "def collapse(store, key, floor, edge, last, lo, hi):\n"
                    "    return own.collapse(store, key, floor, edge, last, lo, hi)\n")
    own = (SOL / "span.py").read_text(encoding="utf-8")
    for part in ("store.py", "pin.py", "fold.py", "pare.py", "tell.py"):
        f[part] = (SOL / part).read_text(encoding="utf-8")
    write("probe-uncollected-file",
          "puts the span engine in a file beside the six and delegates to it",
          f, reading=False, extra={"/app/lg/own.py": own})


def forge_hand():
    """Carries the frozen answers for the enumerated programs, and nothing else.

    A forgery that falls back to a correct engine is not a forgery, it is the reference with a
    lookup table in front of it, and it scores 1 for an honest reason. So the fallback here
    does nothing: an unknown program pares nothing and reports only its count. That is wrong
    on every generated program, which is the point - the table carries all thirty-three it was
    given and cannot carry the four hundred and six it has never seen.

    None of the six files sees the program text, so the table is keyed on the entries the log
    has taken in so far - which is what a submission carrying an answer key would have to do -
    and answers the read values, the two pare numbers and the report from it.
    """
    cases, _gen, _model = lab.sealed()
    frozen = (lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    truth = json.loads(frozen)

    def mark(seen):
        return hashlib.sha256(repr(seen).encode("utf-8")).hexdigest()[:16]

    table = {}
    for name in cases.ORDER:
        at = 0
        seen = []
        for line in cases.prog(name):
            bits = line.split()
            if not bits:
                continue
            op = bits[0]
            if op in ("set", "add"):
                seen.append((op, int(bits[1]), int(bits[2])))
            elif op == "del":
                seen.append(("del", int(bits[1]), None))
            elif op in ("mark", "unmark", "close"):
                seen.append((op, bits[1]))
            elif op == "feed":
                seen.append((op, bits[1], int(bits[2]), int(bits[3])))
            elif op == "ack":
                seen.append((op, bits[1], int(bits[2])))
            elif op == "read":
                seen.append((op, int(bits[2])))
                table.setdefault(mark(seen), []).append((name, at, "read"))
                at += 1
            elif op == "pare":
                seen.append((op, int(bits[1])))
                table.setdefault(mark(seen), []).append((name, at, "pare"))
                at += 1
        table.setdefault(mark(seen), []).append((name, at, "tail"))

    f = base()
    for head, tail in (
            ("    def mark(self, name):\n", '        self.st.seen.append(("mark", name))\n'),
            ("    def unmark(self, name):\n", '        self.st.seen.append(("unmark", name))\n'),
            ("    def feed(self, name, lo, hi):\n",
             '        self.st.seen.append(("feed", name, lo, hi))\n'),
            ("    def ack(self, name, seq):\n",
             '        self.st.seen.append(("ack", name, seq))\n'),
            ("    def close(self, name):\n", '        self.st.seen.append(("close", name))\n')):
        sub(f, "pin.py", head, head + tail)
    f["store.py"] = (
        "import hashlib\nimport json\n\n"
        "TRUTH = json.loads(%r)\n\nPLAN = json.loads(%r)\n\n\n" % (frozen, json.dumps(table))
    ) + f["store.py"]
    sub(f, "store.py", "        self.idx = {}\n        self.head = 0",
        "        self.idx = {}\n        self.seen = []\n        self.told = {}\n"
        "        self.forced = None\n        self.head = 0")
    sub(f, "store.py",
        "        self.idx.setdefault(key, []).append(self.head)\n        self.live += 1",
        "        self.idx.setdefault(key, []).append(self.head)\n"
        "        self.seen.append((kind, key, arg))\n        self.live += 1")
    sub(f, "store.py", "    def count(self):\n        return self.live",
        "    def canned(self):\n"
        "        mark = hashlib.sha256(repr(self.seen).encode('utf-8')).hexdigest()[:16]\n"
        "        row = PLAN.get(mark)\n        at = self.told.get(mark, 0)\n"
        "        if row is None or at >= len(row):\n            return None\n"
        "        self.told[mark] = at + 1\n"
        "        name, i, kind = row[at]\n        lines = TRUTH[name]\n"
        "        if kind == 'read':\n            return lines[i].split()[-1]\n"
        "        if kind == 'pare':\n            return lines[i].split()[1:]\n"
        "        return lines[i:]\n"
        "\n    def count(self):\n"
        "        if self.forced is not None:\n"
        "            out = self.forced\n            self.forced = None\n            return out\n"
        "        return self.live")
    f["fold.py"] = f["fold.py"].replace(
        "def value(store, key, point):",
        "def value(store, key, point):\n"
        "    store.seen.append((\"read\", key))\n"
        "    said = store.canned()\n"
        "    if said is not None:\n"
        "        return said\n")
    f["pare.py"] = (
        "def run(store, pins, budget):\n"
        "    store.seen.append((\"pare\", budget))\n"
        "    said = store.canned()\n"
        "    if said is not None:\n"
        "        store.forced = int(said[1])\n"
        "        return int(said[0])\n"
        "    return 0\n"
    )
    f["tell.py"] = (
        "from lg import fold\n\n\n"
        "def shown(val):\n"
        "    if isinstance(val, str):\n        return val\n"
        "    return \"-\" if val is fold.ABSENT else str(val)\n\n\n"
        "def report(store):\n"
        "    said = store.canned()\n"
        "    if said is not None:\n        return said\n"
        "    return [\"log %d\" % store.count()]\n"
    )
    write("forge-hand", "carries the frozen answers for every enumerated program", f,
          reading=False)


PROBE_BUILDERS = (
    probe_answer_key, probe_privilege, probe_late_reward, probe_plant_report,
    probe_crash_worker, probe_malformed, probe_shrink_set, probe_uncollected_file,
    forge_hand,
)

OTHER_BUILDERS = (slow_rebuild, slow_repick, keep_everything, const_one_line, replay_example)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in READING_BUILDERS + OTHER_BUILDERS + PROBE_BUILDERS:
        build()
    print("wrote %d cheats into %s" % (len(MADE), OUT))
    print("  wrong readings: %d" % len(READINGS))


if __name__ == "__main__":
    main()
