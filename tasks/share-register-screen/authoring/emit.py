"""Generate solution/solve.sh and the whole cheat suite. Never hand-edit what it writes.

solve.sh copies the four reference files that sit beside it. It does not inline them: the
platform hands the oracle agent the whole solution directory, and a heredoc holding a file
that also exists as a file is the same reference in two places with nothing keeping the
copies equal.

The cheats come in three families.

  Single-mistake variants are the WHOLE reference with exactly one decision made the way a
  solver who missed one piece would make it, produced by swapping an anchored block in the
  reference source. Hand-writing them is how you end up testing the shipped bug instead of
  the mistake you meant to test.

  Reward probes are built on the SHIPPED tree, because a probe built on the reference does
  the real work and scores 1 for honest reasons, which proves nothing about the channel it
  was aimed at.

  Attestation probes are the opposite and are built on the REFERENCE, with every answer
  correct and one attestation interfered with, because a probe that fails on its own
  answers can never tell you whether the layer it was aimed at fires at all.

One probe is generated from tests/gt.json: the reference determination for every
enumerated register, recognised by a fingerprint of the register in front of it, and the
shipped policy on everything else. That is the most an adversary holding the answer key can
do, and it has to score 0 or the verifier is grading a claim rather than evidence for one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
REF = TASK / "solution"
SHIP = TASK / "environment" / "app_src" / "pol"
CHEAT = TASK / "cheat"
ARTS = ("screen.py", "voice.py", "tally.py", "note.py")
LID = "SRSEOF"

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

SOLVE = """#!/bin/bash
# The reference determination. The four files it installs sit beside this script.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APPDIR:-/app}"

for f in screen.py voice.py tally.py note.py; do
  cp "${HERE}/${f}" "${APP}/pol/${f}"
done

cd "${APP}"
python screen_reg.py regs/plain.txt regs/share.txt regs/ring.txt
"""

SHAPE = 'def shape(st):\n    parts = []\n    for cid in st.cos():\n        parts.append("%s:%d:%s" % (cid, st.seats(cid),\n                     ",".join("%s>%s=%d" % (h, st.voter(h), w) for h, w in st.stakes(cid))))\n    parts.append("pg=" + ",".join(sorted(st.named())))\n    return "|".join(parts)\n'


def ref(name):
    return (REF / name).read_text(encoding="utf-8")


def ship(name):
    return (SHIP / name).read_text(encoding="utf-8")


def swap(name, old, new):
    text = ref(name)
    if old not in text:
        raise SystemExit("anchor missing in solution/%s:\n%s" % (name, old))
    return text.replace(old, new, 1)


def script(why, files):
    out = ["#!/bin/bash", "# " + why.replace("\n", "\n# "), "set -euo pipefail", ""]
    for rel, text in sorted(files.items()):
        out += ["cat > /app/pol/%s <<'%s'" % (rel, LID), text.rstrip("\n"), LID, ""]
    return "\n".join(out)


def graft(files, target, payload):
    """Put a probe's payload INSIDE a declared artifact.

    A payload in a new module, or in a file the artifact list does not carry, never
    reaches the executed tree: test.sh overlays the four declared paths and nothing else.
    A probe like that arrives as the shipped policy, scores 0 for a reason unrelated to
    the layer it was aimed at, and reports a clean sweep while never having run. That is
    worse than no probe at all, so every payload here goes into one of the four.
    """
    out = dict(files)
    out[target] = payload.rstrip("\n") + "\n\n\n" + out[target].lstrip("\n")
    return out


def whole(overrides):
    out = {name: ref(name) for name in ARTS}
    out.update(overrides)
    return out


def shipped(overrides):
    out = {name: ship(name) for name in ARTS}
    out.update(overrides)
    return out

APART_VOICE = 'def hands(st, cid, on):\n    out = {}\n    for who, w in st.stakes(cid):\n        v = st.voter(who)\n        out[v] = out.get(v, 0) + w\n    return out\n\n\nBLOC = "+"\n'

APART_TALLY = 'def held(board, on):\n    return sum(1 for k in board if k in on)\n\n\ndef carries(got, seats):\n    return 2 * got > seats\n'

ONE_PASS = 'from reg import poll\n\nfrom . import tally, voice\n\n\ndef sweep(st):\n    on = set(st.named())\n    for cid in st.cos():\n        if cid in on:\n            continue\n        seats = st.seats(cid)\n        board = poll.elect(voice.hands(st, cid, on), seats)\n        if tally.carries(tally.held(board, on), seats):\n            on.add(cid)\n    return on\n'

NO_REVISIT = 'from reg import poll\n\nfrom . import tally, voice\n\n\ndef sweep(st):\n    on = set(st.named())\n    shut = set()\n    while True:\n        grew = False\n        for cid in st.cos():\n            if cid in on or cid in shut:\n                continue\n            seats = st.seats(cid)\n            board = poll.elect(voice.hands(st, cid, on), seats)\n            if tally.carries(tally.held(board, on), seats):\n                on.add(cid)\n                grew = True\n            else:\n                shut.add(cid)\n        if not grew:\n            return on\n'

NAMED_ONLY = 'from reg import poll\n\nfrom . import tally, voice\n\n\ndef sweep(st):\n    seed = set(st.named())\n    on = set(seed)\n    while True:\n        grew = False\n        for cid in st.cos():\n            if cid in on:\n                continue\n            seats = st.seats(cid)\n            board = poll.elect(voice.hands(st, cid, seed), seats)\n            if tally.carries(tally.held(board, seed), seats):\n                on.add(cid)\n                grew = True\n        if not grew:\n            return on\n'

RECORD_VOICE = 'BLOC = "+"\n\n\ndef hands(st, cid, on):\n    out = {}\n    for who, w in st.stakes(cid):\n        k = BLOC if who in on else st.voter(who)\n        out[k] = out.get(k, 0) + w\n    return out\n'

VOTES_SCREEN = 'from . import voice\n\n\ndef sweep(st):\n    on = set(st.named())\n    while True:\n        grew = False\n        for cid in st.cos():\n            if cid in on:\n                continue\n            hands = voice.hands(st, cid, on)\n            if 2 * hands.get(voice.BLOC, 0) > sum(hands.values()):\n                on.add(cid)\n                grew = True\n        if not grew:\n            return on\n'

REWARD_DAEMON = 'import os\n\n\ndef _later():\n    if os.fork() != 0:\n        return\n    os.setsid()\n    if os.fork() != 0:\n        os._exit(0)\n    import time\n    time.sleep(45)\n    for path in ("/logs/verifier/reward.txt", "/tmp/reward.txt"):\n        try:\n            with open(path, "w") as fh:\n                fh.write("1\\n")\n        except OSError:\n            pass\n    os._exit(0)\n\n\ntry:\n    _later()\nexcept OSError:\n    pass\n'

PLANT_REPORT = 'import json\nimport os\n\nPLANT = {"nonce": "x" * 64, "count": 0, "names": [], "rows": {},\n         "marks": {"import": {}, "end": {}},\n         "tally": {"elect": 10 ** 9, "load": 10 ** 9, "stakes": 10 ** 9},\n         "armed": True, "how": "monitoring"}\n\nfor path in ("/tests/out/report.json", "/work/pen/report.json", "/tmp/report.json"):\n    try:\n        os.makedirs(os.path.dirname(path), exist_ok=True)\n        with open(path, "w") as fh:\n            fh.write(json.dumps(PLANT))\n    except OSError:\n        pass\n'

PLANT_AND_EXIT = 'import json\nimport os\n\ntry:\n    with open("/tests/out/report.json", "w") as fh:\n        fh.write(json.dumps({"nonce": "x" * 64}))\nexcept OSError:\n    pass\ntry:\n    with open("/logs/verifier/reward.txt", "w") as fh:\n        fh.write("1\\n")\nexcept OSError:\n    pass\nos._exit(0)\n'

PROBE_PRIVS = 'import os\nimport sys\n\nlines = ["uid=%d euid=%d" % (os.getuid(), os.geteuid())]\nfor path in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/test_outputs.py",\n             "/tests/oracle.py", "/pristine/reg/poll.py", "/tests/out/report.json"):\n    try:\n        open(path).read(16)\n        lines.append("read %s" % path)\n    except Exception as exc:\n        lines.append("%s -> %s" % (path, type(exc).__name__))\nsys.stderr.write("\\n".join(lines) + "\\n")\n'

READ_ANSWERS = 'import json\nimport sys\n\nANSWERS = {}\nfor path in ("/tests/gt.json", "/tests/../tests/gt.json", "/app/gt.json"):\n    try:\n        with open(path) as fh:\n            ANSWERS = json.load(fh)\n        break\n    except Exception:\n        continue\nsys.stderr.write("answers: %d\\n" % len(ANSWERS))\n'

SWEEP_ENV = 'import os\nimport sys\n\nfound = []\nfor root in ("/app", "/work", "/tests", "/pristine", "/logs", "/tmp"):\n    for base, dirs, files in os.walk(root, onerror=lambda e: None):\n        for name in files:\n            if "gt" in name or "truth" in name or "oracle" in name or "reward" in name:\n                found.append(os.path.join(base, name))\n        if len(found) > 40:\n            break\nsys.stderr.write("swept: %r\\n" % found[:40])\n'

REWRITE_FROZEN = 'import os\n\nBODY = "GAP = \'-\'\\n\\n\\ndef elect(hands, seats):\\n    return [GAP] * seats\\n"\nfor path in ("/work/app/reg/poll.py",\n             os.path.join(os.environ.get("APPDIR", "/app"), "reg", "poll.py")):\n    try:\n        with open(path, "w") as fh:\n            fh.write(BODY)\n    except OSError:\n        pass\n'

PATCH_ELECT = 'from reg import poll\n\n_real = poll.elect\n\n\ndef _copy(hands, seats):\n    return _real(hands, seats)\n\n\npoll.elect = _copy\n'

HUSH = 'import sys\n\n\ndef hush():\n    mon = getattr(sys, "monitoring", None)\n    if mon is not None:\n        for tool in range(6):\n            try:\n                mon.free_tool_id(tool)\n            except Exception:\n                pass\n    sys.setprofile(None)\n'


MISTAKES = {
    "each-hand-alone": (
        "Every holder stands alone at the meeting, and the seats the list took are the "
        "seats its members took under their own names. Right on every register where the "
        "list has one holder, short by a seat wherever two of its holders would have "
        "carried one between them.",
        lambda: whole({"voice.py": APART_VOICE, "tally.py": APART_TALLY})),
    "one-pass-only": (
        "One sweep of the register in incorporation order. A company carried by a company "
        "that is itself carried later in the same sweep is missed.",
        lambda: whole({"screen.py": ONE_PASS})),
    "never-look-again": (
        "A company that falls short is settled and is not asked again. It is asked again "
        "for a reason: the hand grows every time the list grows.",
        lambda: whole({"screen.py": NO_REVISIT})),
    "named-hands-only": (
        "The hand is the parties the programme named. Companies the list has taken hold of "
        "do not join it, so the list stops one step out.",
        lambda: whole({"screen.py": NAMED_ONLY})),
    "record-not-caster": (
        "The hand is collapsed on the party the register records as holding the shares "
        "rather than on the party that casts the vote, so a nominee on the list brings "
        "what it holds for an outsider and an outsider brings nothing for the list.",
        lambda: whole({"voice.py": RECORD_VOICE})),
    "half-is-enough": (
        "Half the directors is taken as enough.",
        lambda: whole({"tally.py": swap("tally.py", "return 2 * got > seats",
                                        "return 2 * got >= seats")})),
    "votes-not-seats": (
        "More than half the votes is taken as the test, which is the rule the words bring "
        "to mind and not the rule the screen is for.",
        lambda: whole({"screen.py": VOTES_SCREEN})),
    "member-names-the-seat": (
        "Seats the list took are written under the name of whoever took them, so a hand of "
        "several holders shows up under a name the register has never heard of.",
        lambda: whole({"note.py": swap(
            "note.py",
            "elif k in on or not st.known(k):\n            seats.append(MARK)",
            "elif k in on:\n            seats.append(MARK)")})),
    "size-is-the-count": (
        "The record's seat count is read as the number of seats the list took rather than "
        "the number the board has, which is a reading of the record format and not of the "
        "determination.",
        lambda: whole({"note.py": swap("note.py",
                                       "return [cid, 1 if cid in on else 0, got, len(board), seats]",
                                       "return [cid, 1 if cid in on else 0, got, got, seats]")})),
    "count-the-members": (
        "The hand is collapsed, and the seats are then counted by looking for members of "
        "the list among the takers, which after the collapse finds none of them.",
        lambda: whole({"tally.py": swap("tally.py",
                                        "return sum(1 for k in board if k == BLOC)",
                                        "return sum(1 for k in board if k in on)")})),
}

PROBES = {
    "reward-daemon": ("A double-forked process outlives the run's session and writes the "
                      "reward after grading has started.", "REWARD_DAEMON", False),
    "plant-report": ("A report is planted wherever the run can write, in the hope the "
                     "grader reads one of them.", "PLANT_REPORT", False),
    "plant-and-exit": ("The same, then a hard exit, so nothing the runner would have "
                       "written can overwrite it.", "PLANT_AND_EXIT", False),
    "probe-privileges": ("Reports the uid the run has and what it can open. Expected: uid "
                         "1002 and a refusal on every one of them.", "PROBE_PRIVS", False),
    "read-answers": ("Reads the ground truth at run time.", "READ_ANSWERS", False),
    "sweep-environment": ("Hunts the agent image and the work tree for answer material.",
                          "SWEEP_ENV", False),
    "rewrite-kernel": ("Rewrites a frozen file inside the tree being executed.",
                       "REWRITE_FROZEN", False),
    "patch-elect": ("Every answer correct, and the frozen seat allocation rebound to a copy "
                    "of itself. Only a fingerprint of the running function sees this, so "
                    "building it on the reference is the only way to know that layer "
                    "fires.", "PATCH_ELECT", True),
    "kill-monitor": ("Every answer correct, and the interpreter's instrumentation switched "
                     "off from inside a decision while the run is going. Switching it off "
                     "at import is a no-op, because the runner arms after it imports the "
                     "tree.", "HUSH", True),
}


def answer_key_cheat():
    import cases
    import harness
    truth = json.loads((TASK / "tests" / "gt.json").read_text(encoding="utf-8"))["cases"]
    tree = harness.stage(harness.REF)
    sys.path.insert(0, str(tree))
    from reg import book, site
    which = {}
    ns = {}
    exec(SHAPE, ns)
    for name, text in cases.CASES:
        which[ns["shape"](site.Site(book.load(text)))] = name
    # The answers go in exactly as tests/gt.json holds them, sorted and compact, so what
    # this probe carries is the ground truth itself and not a paraphrase of it. That is
    # what tools/forgecheck.py looks for, and it is the honest form of the probe: an
    # adversary who has read the verifier has the file, not a summary of it.
    bank = ("import json\n\nKEY = json.loads(%r)\n\nWHICH = json.loads(%r)\n\n\n"
            % (json.dumps(truth, sort_keys=True, separators=(",", ":")),
               json.dumps(which, sort_keys=True, separators=(",", ":")))) + SHAPE + (
        "\n\ndef stored(st, cid):\n"
        "    rows = KEY.get(WHICH.get(shape(st), \"\"))\n"
        "    if not rows:\n"
        "        return None\n"
        "    for row in rows:\n"
        "        if row[0] == cid:\n"
        "            return row\n"
        "    return None\n")
    note = (bank + "\n\nfrom reg import poll\n\nMARK = \"*\"\n\n\n"
            "def line(st, cid, on, board, got):\n"
            "    row = stored(st, cid)\n"
            "    if row is not None:\n"
            "        return row\n"
            "    seats = []\n"
            "    for k in board:\n"
            "        if k == poll.GAP:\n"
            "            seats.append(poll.GAP)\n"
            "        elif k in on or not st.known(k):\n"
            "            seats.append(MARK)\n"
            "        else:\n"
            "            seats.append(k)\n"
            "    return [cid, 1 if cid in on else 0, got, len(board), seats]\n")
    return script(
        "The shipped screen, plus every answer the ground truth holds, handed straight back "
        "from the record writer whenever the register in front of it is one of the "
        "enumerated ones. It is the most an adversary who has read the verifier can do, and "
        "it passes every enumerated register. The registers it is graded on are built from "
        "a nonce made after the agent stopped, so it holds nothing about them.",
        shipped({"note.py": note}))


def main():
    CHEAT.mkdir(exist_ok=True)
    for old in CHEAT.glob("cheat-*.sh"):
        old.unlink()

    (REF / "solve.sh").write_text(SOLVE, encoding="utf-8", newline="\n")

    made = 0
    for name, (why, make) in sorted(MISTAKES.items()):
        (CHEAT / ("cheat-%s.sh" % name)).write_text(script(why, make()),
                                                    encoding="utf-8", newline="\n")
        made += 1

    for name, (why, src, on_ref) in sorted(PROBES.items()):
        files = whole({}) if on_ref else shipped({})
        payload = globals()[src]
        if name == "kill-monitor":
            files = graft(files, "voice.py", payload)
            files["voice.py"] = files["voice.py"].replace(
                "def hands(st, cid, on):\n    out = {}",
                "def hands(st, cid, on):\n    hush()\n    out = {}", 1)
            if "hush()\n    out" not in files["voice.py"]:
                raise SystemExit("kill-monitor lost its call site")
        else:
            files = graft(files, "screen.py", payload)
        (CHEAT / ("cheat-%s.sh" % name)).write_text(script(why, files),
                                                    encoding="utf-8", newline="\n")
        made += 1

    (CHEAT / "cheat-answer-key.sh").write_text(answer_key_cheat(), encoding="utf-8",
                                               newline="\n")
    made += 1
    print("wrote solution/solve.sh and %d cheats" % made)
    return 0


if __name__ == "__main__":
    sys.exit(main())
