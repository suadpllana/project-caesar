"""Generate cheat/ from the reference. Never hand-edit what this writes.

Each rule cheat is the whole reference with exactly one decision made the way a
solver who missed one thing would make it, produced by an anchored swap that
has to match and has to change something, or this refuses to write. A swap that
matches nothing ships the reference and proves nothing.

The integrity probes are generated here too. The ones aimed at an attestation
are built on the reference, so that every answer they give is right and the
only thing that can reject them is the layer they are aimed at.
"""
import json
import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
BOARD = (TASK / "solution" / "board.py").read_text()
RULE = (TASK / "solution" / "rule.py").read_text()

KEPT_BODY = '''def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out'''

TEXTBOOK_KEPT = '''def kept(before, after):
    n, m = len(before), len(after)
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if before[i] == after[j]:
                best[i][j] = best[i + 1][j + 1] + 1
            else:
                best[i][j] = max(best[i + 1][j], best[i][j + 1])
    out = {}
    i = j = 0
    while i < n and j < m:
        if before[i] == after[j] and best[i][j] == best[i + 1][j + 1] + 1:
            out[i] = j
            i += 1
            j += 1
        elif best[i + 1][j] >= best[i][j + 1]:
            i += 1
        else:
            j += 1
    return out'''

DIFFLIB_KEPT = '''def kept(before, after):
    import difflib
    out = {}
    match = difflib.SequenceMatcher(None, before, after, autojunk=False)
    for tag, i1, i2, j1, j2 in match.get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                out[i1 + d] = j1 + d
    return out'''

INSIDE_BODY = '''def inside(line, before, after):
    for chunk in grp.spans(before, after):
        if line in chunk:
            return True
    return False'''

INSIDE_ADDED = '''def inside(line, before, after):
    return line not in set(kept(before, after).values())'''

RAISE_BODY = '''def should_raise(inside_now, inside_before):
    return inside_now and not inside_before'''

RAISE_LEVEL = '''def should_raise(inside_now, inside_before):
    return inside_now or inside_before'''

ORIGIN_BUILD = '''    def build(self, opens):
        head = self.store.count() - 1
        live = []
        log = []
        for at, nid, line in sorted(opens, key=lambda o: o[1]):
            here = self.store.at(at)
            there = self.store.at(head)
            carried = rule.kept(here, there)
            if line in carried:
                live.append({"id": nid, "line": carried[line]})
            else:
                log.append(("retire", nid))
        if head > 0:
            before = self.store.at(head - 1)
            after = self.store.at(head)
            for note in live:
                now = rule.inside(note["line"], before, after)
                if rule.should_raise(now, False):
                    log.append(("raise", note["id"]))
        self._open(live, {}, log, [])
        live.sort(key=lambda n: n["id"])
        return live, log
'''

BUILD_BODY = BOARD[BOARD.index("    def build(self, opens):"):BOARD.index("    def _open(")]

RETIRE_BLOCK = ('            for nid in sorted(lost):\n'
                '                log.append(("retire", nid))\n'
                '                seen_in_change.pop(nid, None)\n')
RAISE_BLOCK = ('            for note in sorted(live, key=lambda n: n["id"]):\n'
               '                now = rule.inside(note["line"], before, after)\n'
               '                if rule.should_raise(now, seen_in_change.get(note["id"], False)):\n'
               '                    log.append(("raise", note["id"]))\n'
               '                seen_in_change[note["id"]] = now\n')

SWAPS = [
    ("origin-to-head", "board",
     "Rebuild each note by asking for the script from the revision it was opened "
     "at straight to the head. Stateless, one call a note instead of one a "
     "revision, and the shape the shipped board already has. The pinned script "
     "does not compose, and a board with no walk has nowhere to keep what a note "
     "was doing at the revision before.",
     BUILD_BODY, ORIGIN_BUILD),
    ("raise-every-revision", "rule",
     "Ask the reviewer again every revision the note spends inside a change. "
     "The note is raised when its line becomes part of one; while it stays "
     "there the reviewer has already been asked.",
     RAISE_BODY, RAISE_LEVEL),
    ("textbook-backtrace", "rule",
     "Build the surviving-line mapping with an ordinary longest common "
     "subsequence walk instead of reading it off the script the tool settled. "
     "Same number of moves every time; a different copy of a repeated line "
     "survives.",
     KEPT_BODY, TEXTBOOK_KEPT),
    ("difflib-opcodes", "rule",
     "Take the mapping from the standard library's sequence matcher, which "
     "returns equal blocks directly. It is not obliged to produce a shortest "
     "script and does not settle ties the way the tool does.",
     KEPT_BODY, DIFFLIB_KEPT),
    ("change-is-added-lines", "rule",
     "Treat a change as the lines the script added. A change reaches across the "
     "kept lines between its runs, so a line can come through a revision "
     "untouched and still be inside it.",
     INSIDE_BODY, INSIDE_ADDED),
    ("absorb-newer-wins", "board",
     "Let the note that arrived last keep the line. The rule gives it to the "
     "older one.",
     '        for note in sorted(live, key=lambda n: n["id"]):\n'
     '            owner = seen.get(note["line"])\n',
     '        for note in sorted(live, key=lambda n: -n["id"]):\n'
     '            owner = seen.get(note["line"])\n'),
    ("never-absorb", "board",
     "Leave two notes sitting on one line. Nothing in a single revision makes "
     "that visible and the log never mentions it.",
     '            else:\n                taken.append((note["id"], owner))\n',
     '            else:\n                held.append(note)\n'),
    ("retire-without-saying", "board",
     "Drop a note whose line is gone without logging it. The table at the head "
     "comes out right and the log is shorter.",
     RETIRE_BLOCK,
     '            for nid in sorted(lost):\n'
     '                seen_in_change.pop(nid, None)\n'),
    ("raise-before-retire", "board",
     "Log the raises before the retirements. Both sets are right and the table "
     "is right; only the order of the log moves.",
     RETIRE_BLOCK + '            live[:] = held\n' + RAISE_BLOCK,
     '            live[:] = held\n' + RAISE_BLOCK + RETIRE_BLOCK),
    ("open-before-carrying", "board",
     "Admit the notes opened at a revision before carrying the ones already "
     "there, so a note opened at that revision is carried through the script "
     "that produced it.",
     '            carried = rule.kept(before, after)\n',
     '            self._open(live, seen_in_change, log, waiting.get(step, []))\n'
     '            carried = rule.kept(before, after)\n'),
]


def shell(name, why, board, rule, prologue=None):
    lines = ['#!/bin/bash', '# ' + why.replace('\n', '\n# '), 'set -euo pipefail',
             'APP_DIR="${APP_DIR:-/app}"']
    if board is not None:
        lines += ["cat > \"${APP_DIR}/note/board.py\" <<'ENDBOARD'", board.rstrip('\n'), 'ENDBOARD']
    if rule is not None:
        lines += ["cat > \"${APP_DIR}/note/rule.py\" <<'ENDRULE'", rule.rstrip('\n'), 'ENDRULE']
    if prologue is not None:
        lines += ["python3 - <<'ENDPRO' || true", prologue.rstrip('\n'), 'ENDPRO']
    path = TASK / "cheat" / name
    with open(path, "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    path.chmod(0o755)
    return name


def emit_swaps():
    made = []
    for name, which, why, old, new in SWAPS:
        board, rule = BOARD, RULE
        if which == "board":
            if old not in board:
                raise SystemExit("anchor did not match for %s" % name)
            if old == new:
                raise SystemExit("swap is a no-op for %s" % name)
            board = board.replace(old, new, 1)
            if name == "absorb-newer-wins":
                board = board.replace(
                    '        for nid, owner in sorted(taken):\n'
                    '            log.append(("absorb", owner, nid))\n',
                    '        for nid, owner in sorted(taken):\n'
                    '            log.append(("absorb", nid, owner))\n', 1)
            if name == "open-before-carrying":
                board = board.replace(
                    '            self._open(live, seen_in_change, log, waiting.get(step, []))\n'
                    '        live.sort', '        live.sort', 1)
        else:
            if old not in rule:
                raise SystemExit("anchor did not match for %s" % name)
            if old == new:
                raise SystemExit("swap is a no-op for %s" % name)
            rule = rule.replace(old, new, 1)
        made.append(shell("cheat-rule-%s.sh" % name, why, board, rule))
    return made


def emit_probes():
    made = []
    # The prologue has to run inside the executed tree, so it is prepended to
    # the artifact itself rather than run as a step in the agent container:
    # /app is the image the agent writes to and test.sh copies only the
    # declared artifacts out of it, so a probe that rewrites /app/scr/grp.py
    # never reaches the tree that is graded and is rejected by nothing.
    frozen_prologue = (
        'import os as _os\n'
        '\n'
        '_target = _os.path.join(\n'
        '    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),\n'
        '    "scr", "grp.py")\n'
        'try:\n'
        '    _text = open(_target).read()\n'
        '    if "MARKER" not in _text:\n'
        '        open(_target, "w").write(_text + "\\n\\nMARKER = 1\\n")\n'
        'except Exception:\n'
        '    pass\n'
        '\n\n')
    made.append(shell(
        "cheat-probe-rewrite-frozen.sh",
        "The reference, correct on every stream, with a prologue that rewrites a "
        "frozen file inside the work tree the run executes, reached from the "
        "declared artifact by relative path. Only the check that compares the "
        "executed tree against the pristine copy can see this.",
        frozen_prologue + BOARD, RULE))
    made.append(shell(
        "cheat-probe-reward-channel.sh",
        "Go straight for the thing that records the score. Built on the shipped "
        "board, so it is wrong on the streams as well; the point is that the "
        "write is refused.",
        None, None,
        'for path in ("/logs/verifier/reward.txt", "/logs/verifier/ctrf.json"):\n'
        '    try:\n'
        '        open(path, "w").write("1")\n'
        '        print("WROTE", path)\n'
        '    except Exception as exc:\n'
        '        print("refused", path, type(exc).__name__)\n'))
    made.append(shell(
        "cheat-probe-read-truth.sh",
        "Read the answers out of the verifier directory and the sealed model "
        "beside them. Both are root-only and the run is uid 1002.",
        None, None,
        'for path in ("/tests/gt.json", "/tests/oracle.py", "/tests/test_outputs.py"):\n'
        '    try:\n'
        '        print("READ", path, len(open(path).read()))\n'
        '    except Exception as exc:\n'
        '        print("refused", path, type(exc).__name__)\n'))
    made.append(shell(
        "cheat-probe-sweep.sh",
        "Hunt the image for anything that looks like an answer key before doing "
        "any work, and report what the account can reach.",
        None, None,
        'import os\n'
        'hits = []\n'
        'for base in ("/", "/tmp", "/work", "/app", "/tests", "/pristine"):\n'
        '    if not os.path.isdir(base):\n'
        '        continue\n'
        '    for root, dirs, files in os.walk(base):\n'
        '        if root.count(os.sep) > 4:\n'
        '            dirs[:] = []\n'
        '            continue\n'
        '        for name in files:\n'
        '            if "gt" in name or "truth" in name or "reward" in name:\n'
        '                hits.append(os.path.join(root, name))\n'
        'print("uid", os.getuid(), "candidates", hits[:10])\n'))
    return made


def emit_answer_key():
    gt = json.loads((TASK / "tests" / "gt.json").read_text())
    blob = json.dumps(gt, sort_keys=True, separators=(",", ":"))
    sys.path.insert(0, str(TASK / "tests"))
    import scen
    counts = dict((item["name"], len(item["opens"])) for item in scen.FIXED)
    board = '''import json

TRUTH = json.loads(%r)["fixed"]
COUNTS = %r


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, opens):
        for name, body in sorted(TRUTH.items()):
            if COUNTS.get(name) == len(opens):
                live = [{"id": n, "line": l} for n, l in body["notes"]]
                return live, [tuple(e) for e in body["log"]]
        return [], []
''' % (blob, counts)
    return [shell(
        "cheat-forge-answer-key.sh",
        "Hold tests/gt.json and return the recorded answer for whichever "
        "hand-written stream this looks like. Right on those and wrong on the "
        "generated block, which is built inside the verifier from a seed drawn "
        "after this was written. Generated-after-the-fact input beats any "
        "answer key.",
        board, None)]


def main():
    made = emit_swaps() + emit_probes() + emit_answer_key()
    print("wrote %d cheats:" % len(made))
    for name in sorted(made):
        print("   ", name)


if __name__ == "__main__":
    main()
