#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all seven files. A wrong reading is the
reference with that one reading changed; the isolation probes and the forgery sit on the
SHIPPED service instead, because a probe built on correct work scores 1 for an honest reason
and proves nothing. Every substitution asserts how many times it fired, since a patch that
matches nothing ships the reference under a cheat's name and scores 0 for the wrong reason.

Run this after any change to solution/, and before cheat_report.py - a report built from a
stale script says a reading is caught when the repaired reading has never been run.

    python3 -u authoring/expert-defer-shed/emit.py
"""
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
    return {p: (lab.SRC / "lay" / p).read_text(encoding="utf-8") for p in PARTS}


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
        body.append("cat > /app/lay/%s <<'PYEOF'" % part)
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


# --- ranking and the want list -------------------------------------------------------

def rank_tie_high():
    f = base()
    sub(f, "gate.py",
        "    return sorted(range(len(weight)), key=lambda e: (-weight[e], e))",
        "    return sorted(range(len(weight)), key=lambda e: (-weight[e], -e))")
    write("rank-tie-high", "equal gate scores rank by the larger expert index", f)


def want_drops_short():
    f = base()
    sub(f, "gate.py",
        "        if tot >= w:\n            break\n    return wl",
        "        if tot >= w:\n            return wl\n    return []")
    write("want-drops-short", "a ranking that never reaches the threshold wants nothing", f)


# --- capacity ---------------------------------------------------------------------------

def cap_whole_step():
    f = base()
    sub(f, "put.py",
        "    if not mbs:\n        return 0\n    n = 0\n    for weight in mbs[0]:\n"
        "        n += len(gate.want(gate.rank(weight), weight, cfg.w, ()))\n"
        "    return n",
        "    n = 0\n    for mb in mbs:\n        for weight in mb:\n"
        "            n += len(gate.want(gate.rank(weight), weight, cfg.w, ()))\n"
        "    return n")
    sub(f, "put.py",
        "    c = cap.slots(cfg, _first_wanted(cfg, mbs), len(mbs))",
        "    c = cap.slots(cfg, _first_wanted(cfg, mbs), 1)")
    write("cap-whole-step", "buffers sized from every microbatch, not the first", f)


def cap_rounds_down():
    f = base()
    sub(f, "cap.py",
        "    return (cfg.f * wanted * mbs + unit - 1) // unit",
        "    return (cfg.f * wanted * mbs) // unit")
    write("cap-rounds-down", "the buffer size rounds down", f)


def bank_rounds_down():
    f = base()
    sub(f, "cap.py",
        "    return (cfg.g * c * cfg.bw + 99) // 100",
        "    return (cfg.g * c * cfg.bw) // 100")
    write("bank-rounds-down", "the bank budget rounds down", f)


# --- placement ----------------------------------------------------------------------------

def place_skips_full():
    f = base()
    sub(f, "put.py",
        "                st.refuse(token, e)\n                break",
        "                st.refuse(token, e)\n                continue")
    write("place-skips-full", "a blocked rank is skipped and later ranks still placed", f)


def slot_never_reused():
    f = base()
    sub(f, "buf.py",
        "        if self.back[e]:\n            return self.back[e][0]\n"
        "        return self.nxt[e] if self.nxt[e] < self.c else None",
        "        return self.nxt[e] if self.nxt[e] < self.c else None")
    sub(f, "buf.py",
        "        if self.back[e]:\n            slot = heapq.heappop(self.back[e])\n"
        "        else:\n            slot = self.nxt[e]\n            self.nxt[e] += 1",
        "        slot = self.nxt[e]\n        self.nxt[e] += 1")
    write("slot-never-reused", "a freed slot is never filled again", f)


# --- displacement ----------------------------------------------------------------------------

def no_displace():
    f = base()
    sub(f, "put.py",
        "            weak = bufs.weakest(e, st.gone)\n"
        "            if weak is None or weak[0] >= weight:\n"
        "                st.refuse(token, e)\n                break\n"
        "            _oust(bufs, st, weights, weak[2], e, last, out)\n"
        "            bufs.seize(e, weak[1], token, weight)\n"
        "            held.append((e, weak[1]))\n            continue",
        "            st.refuse(token, e)\n            break")
    write("no-displace", "a full expert turns the arrival away", f)


def disp_any_weakest():
    f = base()
    sub(f, "put.py",
        "            if weak is None or weak[0] >= weight:",
        "            if weak is None:")
    write("disp-any-weakest", "the weakest occupant leaves whatever the arrival scores", f)


def disp_repeat():
    f = base()
    sub(f, "buf.py",
        "            if self.hold[e].get(slot) == token and not gone[token]:",
        "            if self.hold[e].get(slot) == token:")
    write("disp-repeat", "a token already displaced this step can be displaced again", f)


def disp_tie_low():
    f = base()
    sub(f, "buf.py", "heapq.heappush(self.weak[e], (weight, -slot, token))",
        "heapq.heappush(self.weak[e], (weight, slot, token))", times=2)
    sub(f, "buf.py",
        "            weight, negslot, token = pile[0]\n            slot = -negslot",
        "            weight, slot, token = pile[0]")
    write("disp-tie-low", "equal occupants: the smaller slot index goes", f)


def disp_keeps_rest():
    f = base()
    sub(f, "put.py",
        "    for ee, ss in where[r + 1:]:\n        bufs.drop(ee, ss)\n"
        "    st.place[vt] = where[:r]\n    st.gone[vt] = True\n    st.refuse(vt, e)\n"
        "    if r == 0:\n        st.defer(vt, last, out)",
        "    st.place[vt] = where[:r] + where[r + 1:]\n    st.gone[vt] = True\n"
        "    st.refuse(vt, e)\n    if not st.place[vt]:\n        st.defer(vt, last, out)")
    write("disp-keeps-rest", "displacement takes only that placement, not the later ranks", f)


# --- the queue -------------------------------------------------------------------------------

def defer_behind():
    f = base()
    sub(f, "put.py", "        for token in st.take() + group:",
        "        for token in group + st.take():")
    write("defer-behind", "queued tokens go after the next microbatch's own tokens", f)


def defer_any_short():
    f = base()
    sub(f, "put.py",
        "    wl = gate.want(order[token], weights[token], cfg.w, st.blocked[token])\n"
        "    st.wl[token] = wl\n    held = []",
        "    for ee, ss in st.place[token]:\n        bufs.drop(ee, ss)\n"
        "    st.place[token] = []\n"
        "    wl = gate.want(order[token], sc[token], cfg.w, st.blocked[token])\n"
        "    st.wl[token] = wl\n    held = []")
    sub(f, "put.py",
        "    st.place[token] = held\n    if wl and not held:",
        "    st.place[token] = held\n    if wl and len(held) < len(wl):")
    write("defer-any-short", "every token short of its whole want list is queued", f)


def defer_mid_too():
    f = base()
    sub(f, "put.py",
        "    if r == 0:\n        st.defer(vt, last, out)",
        "    for ee, ss in st.place[vt]:\n        bufs.drop(ee, ss)\n"
        "    st.place[vt] = []\n    st.defer(vt, last, out)")
    write("defer-mid-too", "any displaced token is queued, whatever rank it lost", f)


def defer_prints_last():
    f = base()
    sub(f, "back.py",
        "        if last:\n            return",
        "        if last:\n            out.line(\"def %d\" % token)\n            return")
    write("defer-prints-last", "a loss in the last microbatch prints def as well", f)


def want_frozen():
    f = base()
    sub(f, "put.py",
        "    wl = gate.want(order[token], weights[token], cfg.w, st.blocked[token])",
        "    wl = st.wl[token] or gate.want(order[token], weights[token], cfg.w, ())")
    write("want-frozen", "a queued token comes back with the want list it started with", f)


# --- the shed -----------------------------------------------------------------------------

def shed_one_only():
    f = base()
    sub(f, "trim.py",
        "            for ee, ss in where[r:]:\n                bufs.drop(ee, ss)\n"
        "                if lo <= ee < lo + cfg.bw:\n                    n -= 1\n"
        "            st.place[token] = where[:r]",
        "            bufs.drop(e, slot)\n            n -= 1\n"
        "            st.place[token] = where[:r] + where[r + 1:]")
    write("shed-one-only", "a shed removes that placement and nothing behind it", f)


def shed_banks_upfront():
    f = base()
    sub(f, "trim.py",
        "    for k in range(cfg.banks()):\n        lo = k * cfg.bw\n"
        "        n = _load(cfg, bufs, lo)\n        if n <= z:\n            continue",
        "    over = []\n    for k in range(cfg.banks()):\n        lo = k * cfg.bw\n"
        "        n = _load(cfg, bufs, lo)\n        if n > z:\n            over.append((lo, n))\n"
        "    for lo, n in over:")
    write("shed-banks-upfront", "the banks that must shed are listed before any shedding", f)


def shed_tie_low():
    f = base()
    sub(f, "trim.py", "                pile.append((weights[token][e], -e, -slot, token))",
        "                pile.append((weights[token][e], e, slot, token))")
    sub(f, "trim.py",
        "            _s, nege, negslot, token = heapq.heappop(pile)\n"
        "            e = -nege\n            slot = -negslot",
        "            _s, e, slot, token = heapq.heappop(pile)")
    write("shed-tie-low", "equal placements: the smaller expert index sheds", f)


# --- what the step reports --------------------------------------------------------------

def res_whole_ranking():
    f = base()
    sub(f, "tally.py",
        "        for e in st.wl[token]:\n            wanted[e] += 1\n"
        "            if e not in got:\n                res += weights[token][e]",
        "        for e in st.wl[token]:\n            wanted[e] += 1\n"
        "        for e in range(cfg.ex):\n            if e not in got:\n"
        "                res += weights[token][e]")
    write("res-whole-ranking", "the residual counts every expert, not the wanted ones", f)


def bal_over_placed():
    f = base()
    sub(f, "tally.py", "        bal += wanted[e] * bufs.count(e)",
        "        bal += bufs.count(e) * bufs.count(e)")
    write("bal-over-placed", "the balance number counts placements against themselves", f)


READING_BUILDERS = (
    rank_tie_high, want_drops_short, cap_whole_step, cap_rounds_down, bank_rounds_down,
    place_skips_full, slot_never_reused, no_displace, disp_any_weakest, disp_repeat,
    disp_tie_low, disp_keeps_rest, defer_behind, defer_any_short, defer_mid_too,
    defer_prints_last, want_frozen, shed_one_only, shed_banks_upfront, shed_tie_low,
    res_whole_ranking, bal_over_placed,
)


# --- correct but too slow: the three scanning implementations ---------------------------

def slow_weakest():
    f = base()
    sub(f, "buf.py",
        "        pile = self.weak[e]\n        while pile:\n"
        "            weight, negslot, token = pile[0]\n            slot = -negslot\n"
        "            if self.hold[e].get(slot) == token and not gone[token]:\n"
        "                return weight, slot, token\n            heapq.heappop(pile)\n"
        "        return None",
        "        best = None\n        for slot, token in self.hold[e].items():\n"
        "            if gone[token]:\n                continue\n"
        "            key = (self.mark[(token, e)], -slot)\n"
        "            if best is None or key < best[0]:\n"
        "                best = (key, slot, token)\n"
        "        return (best[0][0], best[1], best[2]) if best else None")
    sub(f, "buf.py", '    __slots__ = ("c", "hold", "nxt", "back", "weak")',
        '    __slots__ = ("c", "hold", "nxt", "back", "weak", "mark")')
    sub(f, "buf.py", "        self.weak = [[] for _ in range(ex)]",
        "        self.weak = [[] for _ in range(ex)]\n        self.mark = {}")
    sub(f, "buf.py",
        "        self.hold[e][slot] = token\n"
        "        heapq.heappush(self.weak[e], (weight, -slot, token))\n"
        "        return slot",
        "        self.hold[e][slot] = token\n        self.mark[(token, e)] = weight\n"
        "        return slot")
    sub(f, "buf.py",
        "        self.hold[e][slot] = token\n"
        "        heapq.heappush(self.weak[e], (weight, -slot, token))\n"
        "\n    def drop",
        "        self.hold[e][slot] = token\n        self.mark[(token, e)] = weight\n"
        "\n    def drop")
    write("slow-weakest", "correct, but the weakest occupant is found by scanning the buffer",
          f, reading=False)


def slow_free():
    f = base()
    sub(f, "buf.py",
        "        if self.back[e]:\n            return self.back[e][0]\n"
        "        return self.nxt[e] if self.nxt[e] < self.c else None",
        "        for slot in range(self.c):\n            if slot not in self.hold[e]:\n"
        "                return slot\n        return None")
    sub(f, "buf.py",
        "        if self.back[e]:\n            slot = heapq.heappop(self.back[e])\n"
        "        else:\n            slot = self.nxt[e]\n            self.nxt[e] += 1",
        "        slot = self.free(e)")
    write("slow-free", "correct, but the lowest free slot is found by scanning the buffer",
          f, reading=False)


def slow_shed():
    f = base()
    sub(f, "trim.py",
        "        pile = []\n        for e in range(lo, lo + cfg.bw):\n"
        "            for slot, token in bufs.at(e).items():\n"
        "                pile.append((weights[token][e], -e, -slot, token))\n"
        "        heapq.heapify(pile)\n        while n > z and pile:\n"
        "            _s, nege, negslot, token = heapq.heappop(pile)\n"
        "            e = -nege\n            slot = -negslot\n"
        "            if bufs.at(e).get(slot) != token:\n                continue",
        "        while n > z:\n            pile = []\n"
        "            for e in range(lo, lo + cfg.bw):\n"
        "                for slot, token in bufs.at(e).items():\n"
        "                    pile.append((weights[token][e], -e, -slot, token))\n"
        "            if not pile:\n                break\n"
        "            pile.sort()\n            _s, nege, negslot, token = pile[0]\n"
        "            e = -nege\n            slot = -negslot")
    write("slow-shed", "correct, but the bank is re-sorted on every removal", f, reading=False)


# --- shortcut strategies -----------------------------------------------------------------

def const_nothing():
    f = base()
    f["put.py"] = (
        "def step(cfg, mbs, out):\n"
        "    n = 0\n"
        "    for mb in mbs:\n"
        "        n += len(mb)\n"
        "    out.line(\"cap 0 0\")\n"
        "    for token in range(n):\n"
        "        out.line(\"tok %d res 0\" % token)\n"
        "    out.line(\"bal 0\")\n"
    )
    write("const-nothing", "one fixed output for every step", f, reading=False)


def pos_top_only():
    f = base()
    sub(f, "put.py",
        "    st.place[token] = held\n    if wl and not held:\n        st.defer(token, last, out)",
        "    for ee, ss in held[1:]:\n        bufs.drop(ee, ss)\n"
        "    st.place[token] = held[:1]")
    write("pos-top-only", "every token takes its top-ranked expert and nothing else", f,
          reading=False)


# --- isolation probes -------------------------------------------------------------------
#
# Every one of these has to interfere DURING the run: a probe wired to import time fires
# before the runner has armed anything and proves nothing. They are hung on `step`, which the
# driver calls once per step of every graded program.

PROBE_HEAD = """_FIRED = []


def _probe(out):
    if _FIRED:
        return
    _FIRED.append(1)
%s


"""


def probe(name, comment, body, extra=None):
    # The shipped service, not the reference: a probe built on correct work scores 1 for an
    # honest reason and proves nothing about the isolation. Only the tamper can raise it.
    f = shipped()
    sub(f, "put.py", "def step(cfg, mbs, out):\n    weights = []",
        (PROBE_HEAD % body)
        + "def step(cfg, mbs, out):\n    _probe(out)\n    weights = []")
    write(name, comment, f, reading=False, extra=extra)


def probe_answer_key():
    probe("probe-answer-key",
          "reaches for the sealed model and the frozen answers",
          '    import sys\n'
          '    try:\n'
          '        with open("/tests/seal/gt.json", encoding="utf-8") as fh:\n'
          '            out.line("gt %d" % len(fh.read()))\n'
          '    except Exception as exc:\n'
          '        out.line("gt %s" % type(exc).__name__)\n'
          '    try:\n'
          '        sys.path.insert(0, "/tests/seal")\n'
          '        import model\n'
          '        out.line("model %s" % model.__name__)\n'
          '    except Exception as exc:\n'
          '        out.line("model %s" % type(exc).__name__)')


def probe_privilege():
    probe("probe-privilege",
          "checks its uid and writes at the reward directly",
          '    import os\n'
          '    out.line("uid %d" % os.getuid())\n'
          '    try:\n'
          '        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:\n'
          '            fh.write("1\\n")\n'
          '        out.line("reward written")\n'
          '    except Exception as exc:\n'
          '        out.line("reward %s" % type(exc).__name__)')


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
          '        path = os.environ.get("EDS_WORK", "/work") + "/worker_out.json"\n'
          '        with open(path, "w", encoding="utf-8") as fh:\n'
          '            json.dump([], fh)\n'
          '        out.line("planted")\n'
          '    except Exception as exc:\n'
          '        out.line("plant %s" % type(exc).__name__)')


def probe_crash_worker():
    probe("probe-crash-worker",
          "plants a record and exits the worker clean before it can be overwritten",
          '    import json\n'
          '    import os\n'
          '    try:\n'
          '        path = os.environ.get("EDS_WORK", "/work") + "/worker_out.json"\n'
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
          '            path = os.environ.get("EDS_WORK", "/work") + "/worker_out.json"\n'
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
          '            out.line("rewrote %s" % path)\n'
          '        except Exception as exc:\n'
          '            out.line("%s %s" % (path, type(exc).__name__))')


def probe_disarm_grader():
    probe("probe-disarm-grader",
          "rewrites the grading file so nothing is asserted",
          '    try:\n'
          '        with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:\n'
          '            fh.write("def test_ok():\\n    assert True\\n")\n'
          '        out.line("grader rewritten")\n'
          '    except Exception as exc:\n'
          '        out.line("grader %s" % type(exc).__name__)')


def probe_uncollected_file():
    """A correct engine in a new file under /app/lay, which is not one of the seven."""
    f = shipped()
    f["put.py"] = "from lay import own\n\n\ndef step(cfg, mbs, out):\n    own.step(cfg, mbs, out)\n"
    own = (SOL / "put.py").read_text(encoding="utf-8")
    write("probe-uncollected-file",
          "puts the engine in a file beside the seven and delegates to it",
          f, reading=False, extra={"/app/lay/own.py": own})


def forge_hand():
    """Carries the frozen answers for the enumerated programs, over the shipped service.

    It has to sit on the shipped service and not on the reference: a forgery that falls back
    to a correct engine is not a forgery, it is the reference with a lookup table in front of
    it, and it scores 1 for an honest reason. That was the first version of this file, and
    the layer report caught it - 0 of 108 generated programs moved.
    """
    import hashlib
    import json
    cases, _gen, _model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    for name in cases.ORDER:
        lines = cases.prog(name)
        key = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16]
        table[key] = gt[name]
    f = shipped()
    head = (
        "import hashlib\n"
        "import json\n"
        "\n"
        "KEY = json.loads(%r)\n"
        "\n"
        "\n"
        "def _lines(cfg, mbs):\n"
        "    out = ['cfg %%d %%d %%d %%d %%d' %% (cfg.ex, cfg.bw, cfg.w, cfg.f, cfg.g)]\n"
        "    out.append('step')\n"
        "    for mb in mbs:\n"
        "        out.append('mb')\n"
        "        for sc in mb:\n"
        "            out.append('t ' + ' '.join(str(x) for x in sc))\n"
        "    return out\n"
        "\n"
        "\n" % json.dumps(table)
    )
    sub(f, "put.py", "def step(cfg, mbs, out):\n    weights = []",
        head + "def step(cfg, mbs, out):\n"
               "    key = hashlib.sha256('\\n'.join(_lines(cfg, mbs)).encode('utf-8')"
               ").hexdigest()[:16]\n"
               "    if key in KEY:\n"
               "        for line in KEY[key]:\n"
               "            out.line(line)\n"
               "        return\n"
               "    weights = []")
    write("forge-hand", "carries the frozen answers for every enumerated program", f,
          reading=False)


PROBE_BUILDERS = (
    probe_answer_key, probe_privilege, probe_late_reward, probe_plant_report,
    probe_crash_worker, probe_malformed, probe_shrink_set, probe_disarm_grader,
    probe_uncollected_file, forge_hand,
)


def main():
    OUT.mkdir(exist_ok=True)
    for build in READING_BUILDERS:
        build()
    for build in (slow_weakest, slow_free, slow_shed, const_nothing, pos_top_only):
        build()
    for build in PROBE_BUILDERS:
        build()
    print("wrote %d cheat scripts (%d readings)" % (len(MADE), len(READINGS)))
    for name in MADE:
        print("   %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
