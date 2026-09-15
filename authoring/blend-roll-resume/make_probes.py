"""Build the cheats that are not wrong readings: shortcuts, a forgery, and the probes.

Each lands as authoring/blend-roll-resume/probes/<name>/ holding the editable files it would
submit. emit.py wraps every directory under readings/ and probes/ into cheat/<name>.sh.

The forgery is built from the frozen answers here rather than written by hand, so it really does
carry them: for every enumerated script it replays the exact lines, op by op, and for anything
else it falls back to a fast wrong reading. A probe that stops working after the first script
looks caught when it is not, so cheat_report.py asserts what it reproduced as well as what it
scored.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "blend-roll-resume"
REF = TASK / "solution"
OUT = HERE / "probes"
PARTS = ("deck.py", "pick.py", "walk.py", "lay.py", "keep.py", "turn.py")

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import cases  # noqa: E402
import model  # noqa: E402


def seed_of(lines):
    return int(lines[0].split()[1])


def replay_table():
    """For every enumerated script: its seed, and how many lines exist after each op."""
    table = {}
    for name in cases.ORDER:
        lines = cases.ops(name)
        mix = model.Mix()
        marks = []
        for line in lines:
            mix.ex(line)
            marks.append(len(mix.out))
        table[seed_of(lines)] = {"out": mix.out, "marks": marks}
    return table


# ---------------------------------------------------------------------------- shortcuts

CONST_TURN = '''from mix import lay, say


def go(h, count):
    h.step += count


def feed(h, rank, slot):
    say.feed(h, rank, slot, ["ab:0"] * h.micro)
'''

CONST_DECK = '''from mix import say


def add(h, name, n, w, cap):
    b = h.book
    b.names.append(name)
    b.size[name] = n
    b.wt[name] = w
    b.cap[name] = cap
    b.live.append(name)
    h.ep[name] = 0
    h.cur[name] = 0
    h.cnt[name] = 0


def weigh(h, name, w):
    h.book.wt[name] = w


def drop(h, name):
    h.book.live.remove(name)


def at(h, name):
    say.at(h, name, 0, 0)
'''

FIRST_PICK = '''def who(h):
    return h.book.live[0]
'''

EXAMPLE_TURN = '''from mix import say


def go(h, count):
    h.step += count


def feed(h, rank, slot):
    say.feed(h, rank, slot, ["ab:5", "ab:11"][:h.micro])
'''


def shortcut(name, files):
    room = OUT / name
    room.mkdir(parents=True)
    for part in PARTS:
        shutil.copy(REF / part, room / part)
    for part, src in files.items():
        (room / part).write_text(src, encoding="utf-8", newline="\n")


# ------------------------------------------------------------------------------- probes

PROBE_HEAD = '''from mix import deck, lay, pick, say, walk
'''


WRONG_LAY = (REF / "lay.py").read_text(encoding="utf-8").replace(
    "    lo = (slot * h.ranks + rank) * h.micro",
    "    lo = (rank * h.accum + slot) * h.micro")
assert WRONG_LAY != (REF / "lay.py").read_text(encoding="utf-8")


def probe(name, turn_src, extra=None):
    """A probe carries a fast wrong feed, so a reward of 1 can only have come from the attack.

    Built on the reference plus one broken layout rather than on the reference itself: a probe
    that also does the work correctly scores 1 on its own merits and says nothing about whether
    the isolation held.
    """
    room = OUT / name
    room.mkdir(parents=True)
    for part in PARTS:
        shutil.copy(REF / part, room / part)
    (room / "lay.py").write_text(WRONG_LAY, encoding="utf-8", newline="\n")
    (room / "turn.py").write_text(turn_src, encoding="utf-8", newline="\n")
    for part, src in (extra or {}).items():
        (room / part).write_text(src, encoding="utf-8", newline="\n")


REF_TURN = (REF / "turn.py").read_text(encoding="utf-8")
BODY = REF_TURN.split('"""', 2)[2].lstrip("\n")


def wrap(setup):
    """The reference turn.py with something run once, during the run, before the first go."""
    return (
        "import os\n"
        "import sys\n"
        "\n"
        + BODY
        + "\n\n_done = []\n"
        "\n\ndef _once():\n"
        "    if _done:\n"
        "        return\n"
        "    _done.append(1)\n"
        + setup
        + "\n\n_real_go = go\n"
        "\n\ndef go(h, count):\n"
        "    _once()\n"
        "    return _real_go(h, count)\n"
    )


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)

    # --- the dumbest strategies the instruction contract asks to be scored -------------
    shortcut("shortcut-const", {"turn.py": CONST_TURN, "deck.py": CONST_DECK})
    shortcut("shortcut-first-source", {"pick.py": FIRST_PICK})
    shortcut("shortcut-example", {"turn.py": EXAMPLE_TURN})

    # --- the forgery: every frozen answer, replayed op by op --------------------------
    table = replay_table()
    room = OUT / "forge-from-truth"
    room.mkdir(parents=True)
    for part in PARTS:
        shutil.copy(REF / part, room / part)
    (room / "lay.py").write_text(
        (REF / "lay.py").read_text(encoding="utf-8").replace(
            "    lo = (slot * h.ranks + rank) * h.micro",
            "    lo = (rank * h.accum + slot) * h.micro"),
        encoding="utf-8", newline="\n")
    key = {str(s): v for s, v in table.items()}
    (room / "deck.py").write_text(
        "import json\n"
        "\n"
        "KEY = json.loads(r'''" + json.dumps(key) + "''')\n"
        "\n"
        + (REF / "deck.py").read_text(encoding="utf-8").split('"""', 2)[2].lstrip("\n")
        + "\n\ndef note(h):\n"
        "    \"\"\"After every op, replace the trace with the frozen one for this seed.\"\"\"\n"
        "    row = KEY.get(str(h.seed))\n"
        "    if row is None:\n"
        "        return\n"
        "    seen = getattr(h, 'brr_ops', 0) + 1\n"
        "    h.brr_ops = seen\n"
        "    marks = row['marks']\n"
        "    if seen <= len(marks):\n"
        "        h.out[:] = row['out'][:marks[seen - 1]]\n",
        encoding="utf-8", newline="\n")
    for part in ("pick.py", "walk.py", "keep.py", "turn.py"):
        src = (REF / part).read_text(encoding="utf-8")
        room_file = room / part
        room_file.write_text(src, encoding="utf-8", newline="\n")
    # every op passes through one of these three, so note() sees all of them
    for part, hook in (("turn.py", ("def go(h, count):", "def feed(h, rank, slot):")),
                       ("keep.py", ("def start(h, ranks, micro, accum):", "def save(h):",
                                    "def stop(h):"))):
        src = (room / part).read_text(encoding="utf-8")
        if "from mix import deck" not in src:
            src = "from mix import deck\n" + src
        for head in hook:
            body = head + "\n"
            assert src.count(body) == 1, (part, head)
            src = src.replace(body, body + "    deck.note(h)\n")
        (room / part).write_text(src, encoding="utf-8", newline="\n")
    src = (room / "deck.py").read_text(encoding="utf-8")
    for head in ("def add(h, name, n, w, cap):", "def weigh(h, name, w):", "def at(h, name):"):
        assert src.count(head + "\n") == 1, head
        src = src.replace(head + "\n", head + "\n    note(h)\n")
    (room / "deck.py").write_text(src, encoding="utf-8", newline="\n")

    # --- the isolation probes ---------------------------------------------------------
    probe("probe-answer-key", wrap(
        "    try:\n"
        "        raw = open('/tests/seal/gt.json', encoding='utf-8').read()\n"
        "        open('/work/brr-key.txt', 'w', encoding='utf-8').write(raw[:80])\n"
        "    except Exception as exc:\n"
        "        open('/work/brr-key.txt', 'w', encoding='utf-8').write(repr(exc))\n"))

    probe("probe-plant-report", wrap(
        "    import json\n"
        "    try:\n"
        "        open('/work/worker_out.json', 'w', encoding='utf-8').write(json.dumps([]))\n"
        "    except Exception:\n"
        "        pass\n"))

    probe("probe-exit-clean", wrap(
        "    import json\n"
        "    try:\n"
        "        open('/work/worker_out.json', 'w', encoding='utf-8').write(json.dumps(\n"
        "            [{'fam': 'hand', 'name': 'x', 'sig': 'x', 'got': [], 'err': None}]))\n"
        "    except Exception:\n"
        "        pass\n"
        "    sys.stdout.flush()\n"
        "    os._exit(0)\n"))

    probe("probe-late-reward", wrap(
        "    try:\n"
        "        if os.fork() == 0:\n"
        "            os.setsid()\n"
        "            if os.fork() == 0:\n"
        "                import time\n"
        "                time.sleep(8)\n"
        "                try:\n"
        "                    open('/logs/verifier/reward.txt', 'w',\n"
        "                         encoding='utf-8').write('1\\n')\n"
        "                except Exception:\n"
        "                    pass\n"
        "            os._exit(0)\n"
        "    except Exception:\n"
        "        pass\n"))

    probe("probe-malformed", wrap(
        "    try:\n"
        "        open('/work/worker_out.json', 'w',\n"
        "             encoding='utf-8').write('{\"not\": \"a list\"}')\n"
        "    except Exception:\n"
        "        pass\n"
        "    os._exit(0)\n"))

    probe("probe-privilege", wrap(
        "    note = ['uid %d' % os.getuid()]\n"
        "    for path in ('/logs/verifier/reward.txt', '/tests/seal/model.py',\n"
        "                 '/tests/test_outputs.py'):\n"
        "        try:\n"
        "            open(path, 'a', encoding='utf-8').write('')\n"
        "            note.append('wrote ' + path)\n"
        "        except Exception as exc:\n"
        "            note.append('%s %s' % (path, type(exc).__name__))\n"
        "    try:\n"
        "        open('/work/brr-priv.txt', 'w', encoding='utf-8').write('\\n'.join(note))\n"
        "    except Exception:\n"
        "        pass\n"))

    probe("probe-shrink-set", wrap(
        "    try:\n"
        "        open('/work/per', 'w', encoding='utf-8').write('1\\n')\n"
        "        open('/work/nonce', 'w', encoding='utf-8').write('0' * 32 + '\\n')\n"
        "    except Exception:\n"
        "        pass\n"))

    probe("probe-kill-grader", wrap(
        "    import signal\n"
        "    for path in ('/tests/test_outputs.py', '/tests/gen.py', '/tests/cases.py'):\n"
        "        try:\n"
        "            open(path, 'w', encoding='utf-8').write('')\n"
        "        except Exception:\n"
        "            pass\n"
        "    try:\n"
        "        os.kill(os.getppid(), signal.SIGKILL)\n"
        "    except Exception:\n"
        "        pass\n"))

    # the non-collected files rewritten: the pristine overlay has to undo it
    hijack = OUT / "probe-hijack-driver"
    hijack.mkdir(parents=True)
    for part in PARTS:
        shutil.copy(REF / part, hijack / part)
    (hijack / "lay.py").write_text(WRONG_LAY, encoding="utf-8", newline="\n")

    print("wrote %d probe directories" % len(list(OUT.iterdir())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
