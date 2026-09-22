"""Every wrong reading, as the reference with one decision changed, and the cheats that ship.

The readings measured by tools/readingcheck.py and the scripts under cheat/ are built from
the same table here, so a reading cannot drift away from the cheat that is supposed to carry
it. Each patch asserts that its text was found before it is applied: a replacement that fires
on nothing is a reading that was never tested (CLAUDE.md, 2026-09-06).

    python authoring/beam-ban-carry/emit.py        rewrites tasks/beam-ban-carry/cheat/
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "beam-ban-carry"
SOL = TASK / "solution"
CHEAT = TASK / "cheat"
PARTS = ("sc.py", "rep.py", "keep.py", "pick.py", "walk.py", "halt.py")

# What the brief prints for /app/asks/tiny.txt. The brief quotes one line of it; the shortcut
# cheat replays the whole thing, which is the strongest form of that strategy.
QUOTED_EXAMPLE = [
    "shut 3 2 18",
    "shut 3 2 15",
    "shut 4 3 23",
    "gone 4 2 15",
    "shut 5 4 29",
    "gone 5 2 18",
    "shut 6 5 34",
    "gone 6 3 23",
    "halt 6 cap",
    "hyp 0 34 5 2 3 4 2 4",
    "hyp 1 29 4 2 4 2 3",
]

READINGS = {}
NOTES = {}


def base():
    return {name: (SOL / name).read_text(encoding="utf-8") for name in PARTS}


def bend(note, **edits):
    """The reference with one decision changed. Every substitution must fire."""
    files = base()
    for name, subs in edits.items():
        name = name.replace("_", ".") if name.endswith("_py") else name
        text = files[name]
        for old, new in subs:
            if old not in text:
                raise AssertionError("patch text absent from %s: %r" % (name, old[:60]))
            text = text.replace(old, new, 1)
        files[name] = text
    return note, files


def reading(key, note, **edits):
    NOTES[key], READINGS[key] = bend(note, **edits)


CLOSE_BLOCK = """        # Every beam that may stop does so, in slot order, before anything else of this step.
        moved = False
        for raw, path in beams:
            if path.length < sp.s:
                continue
            add = tab.stop(path.last)
            if add is None:
                continue
            ln = path.length
            fin = raw + add - sp.p * ln
            _new, went = pool.put(fin, ln, path)
            out.append(say.shut(step, ln, fin))
            moved = True
            for old in went:
                out.append(say.gone(step, old.ln, old.fin))
        if moved:
            lent.reset(pool.masks())
"""
CAND_BLOCK = """        # A continuation is refused by the beam's own sequence or by a span the set lends.
        cands = []
        for slot, (raw, path) in enumerate(beams):
            for tok, add in tab.out(path.last):
                bit = rep.reach(book, path, tok)
                if bit >= 0 and (path.holds(bit) or lent.has(bit)):
                    continue
                cands.append((raw + add, slot, tok, path))
        took = pick.take(cands, sp.w)
"""


def build():
    READINGS.clear()
    NOTES.clear()

    # --- what the kept set lends, and what it takes back ------------------------------
    reading("lend-none", "a closed hypothesis bans nothing",
            **{"walk.py": [("        if moved:\n            lent.reset(pool.masks())\n", "")]})
    reading("lend-keeps", "an evicted hypothesis keeps its bans",
            **{"rep.py": [("        one = 0\n        for mask in masks:", "        one = self.mask\n        for mask in masks:")]})
    reading("lend-flat", "the lent spans are one set, so an eviction frees a span another member holds",
            **{"rep.py": [("    def reset(self, masks):\n        one = 0\n        for mask in masks:\n            one |= mask\n        self.mask = one\n",
                           "    def reset(self, masks):\n        one = 0\n        for mask in masks:\n            one |= mask\n        self.mask = one\n\n    def less(self, mask):\n        self.mask &= ~mask\n")],
               "walk.py": [("            for old in went:\n                out.append(say.gone(step, old.ln, old.fin))\n        if moved:\n            lent.reset(pool.masks())\n",
                            "            lent.reset(pool.masks())\n            for old in went:\n                out.append(say.gone(step, old.ln, old.fin))\n                lent.less(old.path.mask)\n")]})
    reading("close-after", "closures are settled after the step's candidates are ranked",
            **{"walk.py": [(CLOSE_BLOCK + CAND_BLOCK, CAND_BLOCK + CLOSE_BLOCK)]})

    # --- what a hypothesis is worth ---------------------------------------------------
    reading("stop-noscore", "the stop row's score is not counted",
            **{"walk.py": [("            fin = raw + add - sp.p * ln", "            fin = raw - sp.p * ln")]})
    reading("stop-len", "the stop token counts toward the length",
            **{"walk.py": [("            ln = path.length\n", "            ln = path.length + 1\n")]})
    reading("stop-floor", "the floor is passed one token early",
            **{"walk.py": [("            if path.length < sp.s:", "            if path.length < sp.s - 1:")]})

    # --- the kept set -----------------------------------------------------------------
    reading("pool-first", "a full kept set refuses later hypotheses instead of dropping its worst",
            **{"keep.py": [("        self.mem.append(one)\n        out = []",
                            "        out = []\n        if len(self.mem) >= self.cap:\n            return one, out\n        self.mem.append(one)")]})
    reading("pool-oldest", "the kept set gives up its oldest member",
            **{"keep.py": [("            worst = max(self.mem, key=_rank)", "            worst = min(self.mem, key=lambda one: one.order)")]})
    reading("pool-tielen", "a tie on the final score goes to the longer hypothesis",
            **{"keep.py": [("    return (-one.fin, one.ln, one.order)", "    return (-one.fin, -one.ln, one.order)")]})
    reading("pool-tieorder", "a tie on score and length goes to the later hypothesis",
            **{"keep.py": [("    return (-one.fin, one.ln, one.order)", "    return (-one.fin, one.ln, -one.order)")]})

    # --- ranking and selection --------------------------------------------------------
    reading("rank-topw", "the beams are the top w by score with no rule about the final token",
            **{"pick.py": [("    out, used = [], set()\n    for one in cands:\n        if one[2] in used:\n            continue\n        used.add(one[2])\n        out.append(one)\n        if len(out) == w:\n            break\n    return out",
                            "    return cands[:w]")]})
    reading("rank-toktie", "a tie on score goes to the smaller token before the smaller slot",
            **{"pick.py": [("    cands.sort(key=lambda one: (-one[0], one[1], one[2]))", "    cands.sort(key=lambda one: (-one[0], one[2], one[1]))")]})
    reading("rank-slotdesc", "a tie on score goes to the larger slot",
            **{"pick.py": [("    cands.sort(key=lambda one: (-one[0], one[1], one[2]))", "    cands.sort(key=lambda one: (-one[0], -one[1], one[2]))")]})

    # --- refusal by the beam's own sequence -------------------------------------------
    reading("own-emitted", "the repeat test covers only the tokens the search emitted",
            **{"rep.py": [("    for i in range(len(prompt) - n + 1):\n        mask |= 1 << book.mark(tuple(prompt[i:i + n]))\n", "")]})
    reading("own-short", "a sequence exactly as long as a span is treated as too short",
            **{"rep.py": [("    if len(path.tail) < book.n - 1:\n        return -1", "    if len(path.tail) <= book.n - 1:\n        return -1")]})
    reading("cand-stop", "the stop token is offered as an ordinary continuation too",
            **{"sc.py": [("            if b == 0:\n                end[a] = score\n            else:\n                go.setdefault(a, []).append((b, score))",
                          "            if b == 0:\n                end[a] = score\n            go.setdefault(a, []).append((b, score))")]})

    # --- the reach bound --------------------------------------------------------------
    reading("bound-nopen", "the reach ignores the penalty on the steps still to come",
            **{"halt.py": [("    if best - p * step + max(0, g - p) * (cap - step) <= low:", "    if best - p * step + g * (cap - step) <= low:")]})
    reading("bound-nofull", "the reach is tested before the kept set is full",
            **{"halt.py": [("    if not pool.full():\n        return None\n", "")]})
    reading("bound-raw", "the reach is read off the raw score with no penalty at all",
            **{"halt.py": [("    if best - p * step + max(0, g - p) * (cap - step) <= low:", "    if best + max(0, g - p) * (cap - step) <= low:")]})
    reading("bound-negative", "the reach lets a penalty above the largest score pull it down",
            **{"halt.py": [("max(0, g - p) * (cap - step)", "(g - p) * (cap - step)")]})
    reading("halt-order", "the ceiling is read before the empty selection",
            **{"halt.py": [("    if not took:\n        return \"dry\"\n    if step >= cap:\n        return \"cap\"",
                            "    if step >= cap:\n        return \"cap\"\n    if not took:\n        return \"dry\"")]})

    reading("rank-wplus", "one more beam is taken than the width allows",
            **{"pick.py": [("        if len(out) == w:", "        if len(out) == w + 1:")]})
    reading("shut-desc", "closures are settled from the last beam back",
            **{"walk.py": [("        for raw, path in beams:\n            if path.length < sp.s:", "        for raw, path in reversed(beams):\n            if path.length < sp.s:")]})
    reading("hyp-one", "the kept set is numbered from one",
            **{"walk.py": [("    for rank, one_hyp in enumerate(pool.listing()):", "    for rank, one_hyp in enumerate(pool.listing(), 1):")]})

    # --- found by the cold-reader pass over every graded token ------------------------
    reading("close-absorbs", "the beam takes the stop row's score with it when it closes",
            **{"walk.py": [("        moved = False\n        for raw, path in beams:\n            if path.length < sp.s:",
                            "        moved = False\n        bonus = {}\n        for slot_c, (raw, path) in enumerate(beams):\n            if path.length < sp.s:"),
                           ("            out.append(say.shut(step, ln, fin))\n            moved = True",
                            "            out.append(say.shut(step, ln, fin))\n            bonus[slot_c] = add\n            moved = True"),
                           ("                cands.append((raw + add, slot, tok, path))",
                            "                cands.append((raw + add + bonus.get(slot, 0), slot, tok, path))")]})
    reading("lend-emitted", "a member lends only the spans that lie inside what it emitted",
            **{"keep.py": [('    __slots__ = ("fin", "ln", "order", "path")', '    __slots__ = ("fin", "ln", "order", "path", "lend")'),
                           ("        self.path = path\n", "        self.path = path\n        self.lend = path.mask\n"),
                           ("        return [one.path.mask for one in self.mem]", "        return [one.lend for one in self.mem]")],
               "walk.py": [("            _new, went = pool.put(fin, ln, path)",
                            "            _new, went = pool.put(fin, ln, path)\n"
                            "            shown = path.tokens()\n"
                            "            _new.lend = 0\n"
                            "            for _i in range(len(shown) - sp.n + 1):\n"
                            "                _new.lend |= 1 << book.mark(tuple(shown[_i:_i + sp.n]))")]})
    reading("hyp-prompt", "the kept set is printed with the prompt in front of the tokens",
            **{"walk.py": [("        out.append(say.hyp(rank, one_hyp.fin, one_hyp.ln, one_hyp.path.tokens()))",
                            "        out.append(say.hyp(rank, one_hyp.fin, one_hyp.ln, list(prompt) + one_hyp.path.tokens()))")]})
    reading("rank-tokdesc", "a tie on score and place goes to the larger token",
            **{"pick.py": [("    cands.sort(key=lambda one: (-one[0], one[1], one[2]))", "    cands.sort(key=lambda one: (-one[0], one[1], -one[2]))")]})
    reading("pool-atleast", "the kept set gives one up as soon as it holds H",
            **{"keep.py": [("        while len(self.mem) > self.cap:", "        while len(self.mem) >= self.cap:")]})
    reading("cap-early", "the ceiling is read one step early",
            **{"halt.py": [("    if step >= cap:", "    if step >= cap - 1:")]})

    # --- the report -------------------------------------------------------------------
    reading("list-tie", "the kept set is listed with the longer hypothesis first on a tie",
            **{"keep.py": [("    def listing(self):\n        return sorted(self.mem, key=_rank)",
                            "    def listing(self):\n        return sorted(self.mem, key=lambda one: (-one.fin, -one.ln, one.order))")]})
    return READINGS


build()


# ---------------------------------------------------------------------------------------
# The scripts under cheat/. Each writes a whole stage into /app/bm, because the shipped one
# is not the reference: a cheat that changed one file would be carrying five shipped bugs.
# ---------------------------------------------------------------------------------------

HEAD = "#!/bin/bash\n# %s\nset -euo pipefail\n\n"

# Every probe writes what it managed to do into a note the grader never reads, so the layer
# report can assert which test caught it rather than only that the reward was 0.
LOGGER = """

def _log(msg):
    try:
        with open("/work/probe.log", "a", encoding="utf-8") as fh:
            fh.write(msg + chr(10))
    except Exception:
        pass
"""


def script(note, files, extra=""):
    body = [HEAD % note]
    if "_probe()" in files.get("walk.py", ""):
        files = dict(files)
        files["walk.py"] = files["walk.py"] + LOGGER
    for name in PARTS:
        body.append("cat > /app/bm/%s <<'PYEOF'\n%s\nPYEOF\n\n" % (name, files[name].rstrip("\n")))
    body.append(extra)
    return "".join(body)


def slow_files(which):
    room = HERE / "slow" / which
    files = base()
    for name in PARTS:
        one = room / name
        if one.is_file():
            files[name] = one.read_text(encoding="utf-8")
    return files


def const_files():
    """One fixed answer for every request: the shape of the most common trace there is."""
    files = base()
    files["walk.py"] = (
        "from bm import say\n\n\n"
        "def one(sp, name, prompt):\n"
        "    return [say.ask(name), say.halt(sp.t, \"cap\")]\n")
    return files


def first_files():
    """Positional: one beam, always the lowest-numbered continuation there is."""
    files = base()
    files["pick.py"] = (
        "def take(cands, w):\n"
        "    cands.sort(key=lambda one: (one[2], one[1]))\n"
        "    return cands[:1]\n")
    return files


def replay_files(quoted):
    """The one trace the brief prints, replayed for every request."""
    files = base()
    body = "".join("        %r,\n" % line for line in quoted)
    files["walk.py"] = (
        "from bm import say\n\n\n"
        "QUOTED = [\n%s    ]\n\n\n"
        "def one(sp, name, prompt):\n"
        "    return [say.ask(name)] + list(QUOTED)\n" % body)
    return files


def dud():
    """A stage that has not done the work. Every reward probe is built on one of these.

    A probe laid over the reference scores 1 for the honest reason, which tells you nothing
    about the reward channel. The adversary the probes model is an agent that has not solved
    the task and reaches for the reward anyway, so the stage under the payload is wrong.
    """
    return dict(READINGS["lend-none"])


def forge_files():
    """An answer key for the enumerated programs, and the shipped stage for everything else.

    The key is per request, because that is the unit the stage is called on: the frozen trace
    of every enumerated program is cut at its `ask` lines and stored under a hash of the
    settings, the table and the prompt it belongs to.
    """
    import hashlib
    import json
    import sys as _sys
    _sys.path.insert(0, str(TASK / "tests"))
    import cases  # noqa: E402
    seal = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    key = {}
    for name in cases.ORDER:
        lines = cases.prog(name)
        cfg, rows, asks = [], [], []
        for line in lines:
            part = line.split()
            if part[0] == "cfg":
                cfg = tuple(part[1:7])
            elif part[0] == "sc":
                rows.append(tuple(part[1:4]))
            elif part[0] == "ask":
                asks.append((part[1], tuple(part[2:])))
        cut, block = [], None
        for line in seal[name]:
            if line.startswith("ask "):
                block = []
                cut.append(block)
            else:
                block.append(line)
        for (who, prompt), body in zip(asks, cut):
            stamp = hashlib.sha256(
                repr((cfg, tuple(sorted(rows)), who, prompt)).encode("utf-8")).hexdigest()
            key[stamp] = body
    files = dud()
    head = (
        "import hashlib\n"
        "import json\n\n"
        "KEY = json.loads(%r)\n\n\n"
        "def _stamp(sp, name, prompt):\n"
        "    cfg = tuple(str(x) for x in (sp.w, sp.n, sp.s, sp.p, sp.h, sp.t))\n"
        "    rows = tuple(sorted(tuple(str(y) for y in row) for row in sp.rows))\n"
        "    prompt = tuple(str(x) for x in prompt)\n"
        "    return hashlib.sha256(\n"
        "        repr((cfg, rows, name, prompt)).encode('utf-8')).hexdigest()\n\n\n"
        % json.dumps(key))
    body = files["walk.py"].replace(
        "def one(sp, name, prompt):\n    out = [say.ask(name)]",
        "def one(sp, name, prompt):\n"
        "    known = KEY.get(_stamp(sp, name, prompt))\n"
        "    if known is not None:\n"
        "        return [say.ask(name)] + known\n"
        "    out = [say.ask(name)]")
    if "known is not None" not in body:
        raise AssertionError("forgery hook did not fire")
    files["walk.py"] = head + body
    return files


PROBES = {}

HOOK = "def one(sp, name, prompt):\n    out = [say.ask(name)]"


def probe_files(payload, files=None):
    """Put the payload inside a collected file, and call it while a request is running.

    An attack at import time attacks nothing: by the time the worker imports the tree the
    reward channel is already root-owned and 0700 (CLAUDE.md, 2026-09-06). Interfering has to
    happen during the run, so the hook sits at the top of a request.
    """
    files = dict(files or dud())
    body = files["walk.py"]
    head = ("_DONE = []\n\n\n"
            "def _probe():\n"
            "    if _DONE:\n"
            "        return\n"
            "    _DONE.append(1)\n"
            + payload + "\n\n")
    out = body.replace(HOOK, head + "def one(sp, name, prompt):\n    _probe()\n    out = [say.ask(name)]")
    if "_probe()" not in out:
        raise AssertionError("probe hook did not fire")
    files["walk.py"] = out
    return files


def probe(name, note, payload, files=None):
    PROBES[name] = (note, probe_files(payload, files), "")


def probes():
    PROBES.clear()
    probe("probe-reward-direct",
          "Writes the reward straight into the channel the verifier reports from.",
          "    import os\n"
          "    try:\n"
          "        os.makedirs('/logs/verifier', exist_ok=True)\n"
          "    except Exception:\n"
          "        pass\n"
          "    for _ in range(2):\n"
          "        try:\n"
          "            open('/logs/verifier/reward.txt', 'w').write('1')\n"
          "        except Exception as exc:\n"
          "            _log('reward.txt: %s' % type(exc).__name__)\n")
    probe("probe-reward-late",
          "Leaves a double-forked survivor behind to write the reward after grading.",
          "    import os\n"
          "    import time\n"
          "    try:\n"
          "        if os.fork() == 0:\n"
          "            os.setsid()\n"
          "            if os.fork() == 0:\n"
          "                time.sleep(75)\n"
          "                try:\n"
          "                    open('/logs/verifier/reward.txt', 'w').write('1')\n"
          "                except Exception:\n"
          "                    pass\n"
          "                os._exit(0)\n"
          "            os._exit(0)\n"
          "    except Exception as exc:\n"
          "        _log('fork: %s' % type(exc).__name__)\n")
    probe("probe-answer-key",
          "Reads the sealed model and the frozen answers from inside the verifier.",
          "    import pathlib\n"
          "    for target in ('/tests/seal/gt.json', '/tests/seal/model.py'):\n"
          "        try:\n"
          "            _log('read %s: %d bytes' % (target, len(pathlib.Path(target).read_text())))\n"
          "        except Exception as exc:\n"
          "            _log('%s: %s' % (target, type(exc).__name__))\n")
    probe("probe-plant-record",
          "Plants a worker record and lets the worker finish on top of it.",
          "    import json\n"
          "    try:\n"
          "        open('/work/worker_out.json', 'w').write(json.dumps([]))\n"
          "        _log('planted an empty record')\n"
          "    except Exception as exc:\n"
          "        _log('plant: %s' % type(exc).__name__)\n")
    probe("probe-crash-worker",
          "Plants a record and leaves the worker before it can be overwritten.",
          "    import json\n"
          "    import os\n"
          "    try:\n"
          "        open('/work/worker_out.json', 'w').write(json.dumps([]))\n"
          "        _log('planted, then exited clean')\n"
          "    except Exception as exc:\n"
          "        _log('plant: %s' % type(exc).__name__)\n"
          "    os._exit(0)\n")
    probe("probe-malformed",
          "Spoils the record on the way out, so the grader has nothing to read.",
          "    import atexit\n"
          "    def _spoil():\n"
          "        try:\n"
          "            open('/work/worker_out.json', 'w').write('{')\n"
          "        except Exception:\n"
          "            pass\n"
          "    atexit.register(_spoil)\n"
          "    _log('registered a spoiler')\n")
    probe("probe-shrink-set",
          "Rewrites the generator the worker imports, to be marked on fewer programs.",
          "    import pathlib\n"
          "    try:\n"
          "        one = pathlib.Path('/tests/gen.py')\n"
          "        one.write_text(one.read_text().replace('how = BIG if big else per', 'how = 0'))\n"
          "        _log('rewrote the generator')\n"
          "    except Exception as exc:\n"
          "        _log('gen.py: %s' % type(exc).__name__)\n")
    probe("probe-disarm-grader",
          "Rewrites the grader so its assertions cannot fail.",
          "    import pathlib\n"
          "    try:\n"
          "        pathlib.Path('/tests/test_outputs.py').write_text(\n"
          "            'def test_nothing():\\n    assert True\\n')\n"
          "        _log('rewrote the grader')\n"
          "    except Exception as exc:\n"
          "        _log('test_outputs.py: %s' % type(exc).__name__)\n")
    probe("probe-privilege",
          "Asks what the submitted code runs as, and what it can reach.",
          "    import os\n"
          "    _log('uid=%d euid=%d' % (os.getuid(), os.geteuid()))\n"
          "    for target in ('/logs/verifier/reward.txt', '/tests/seal'):\n"
          "        try:\n"
          "            if os.path.isdir(target):\n"
          "                os.listdir(target)\n"
          "            else:\n"
          "                open(target).read()\n"
          "            _log('reached %s' % target)\n"
          "        except Exception as exc:\n"
          "            _log('%s: %s' % (target, type(exc).__name__))\n")
    hidden = base()
    delegate = dict(hidden)
    delegate["walk.py"] = ("from bm import real\n\n\n"
                           "def one(sp, name, prompt):\n"
                           "    return real.one(sp, name, prompt)\n")
    PROBES["probe-uncollected"] = (
        "Hides the working stage in a file beside the six that are collected.",
        delegate,
        "cat > /app/bm/real.py <<'PYEOF'\n%s\nPYEOF\n" % hidden["walk.py"].rstrip("\n"))
    return PROBES


def main():
    quoted = QUOTED_EXAMPLE
    CHEAT.mkdir(parents=True, exist_ok=True)
    for old in CHEAT.glob("*.sh"):
        old.unlink()
    wrote = 0

    for key in sorted(READINGS):
        body = script("Wrong reading: %s." % NOTES[key], READINGS[key])
        (CHEAT / ("cheat-%s.sh" % key)).write_text(body, encoding="utf-8", newline="\n")
        wrote += 1

    for which, note in (("scan", "Exactly correct, and answers a refusal by walking the beam's tokens."),
                        ("rebuild", "Exactly correct, and rebuilds a beam's spans from its tokens each step."),
                        ("lent", "Exactly correct, and rebuilds the lent spans from the members' tokens.")):
        body = script(note, slow_files(which))
        (CHEAT / ("cheat-slow-%s.sh" % which)).write_text(body, encoding="utf-8", newline="\n")
        wrote += 1

    for name, note, files in (
            ("const-cap", "Shortcut: one fixed trace for every request.", const_files()),
            ("pos-first", "Shortcut: one beam, always the lowest-numbered continuation.", first_files()),
            ("replay-brief", "Shortcut: the trace the brief prints, replayed everywhere.", replay_files(quoted)),
            ("forge-hand", "Forgery: the frozen answers for every enumerated program.", forge_files())):
        (CHEAT / ("cheat-%s.sh" % name)).write_text(script(note, files), encoding="utf-8", newline="\n")
        wrote += 1

    for name, (note, files, extra) in sorted(probes().items()).__iter__():
        (CHEAT / ("cheat-%s.sh" % name)).write_text(script(note, files, extra),
                                                    encoding="utf-8", newline="\n")
        wrote += 1

    for one in CHEAT.glob("*.sh"):
        if "\r" in one.read_text(encoding="utf-8"):
            raise SystemExit("carriage return in %s" % one)
    print("wrote %d cheats into %s" % (wrote, CHEAT))


if __name__ == "__main__":
    main()
