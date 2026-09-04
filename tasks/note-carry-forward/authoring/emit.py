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

KEPT_BODY = """def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out"""

TEXTBOOK_KEPT = """def kept(before, after):
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
    return out"""

DIFFLIB_KEPT = """def kept(before, after):
    import difflib
    out = {}
    match = difflib.SequenceMatcher(None, before, after, autojunk=False)
    for tag, i1, i2, j1, j2 in match.get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                out[i1 + d] = j1 + d
    return out"""

TOUCHED_BODY = """def touched(span, before, after):
    for chunk in grp.spans(before, after):
        if span & chunk:
            return True
    return False"""

TOUCHED_ALL = """def touched(span, before, after):
    reached = set()
    for chunk in grp.spans(before, after):
        reached |= chunk
    return bool(span) and span <= reached"""

TOUCHED_ADDED = """def touched(span, before, after):
    landed = set(kept(before, after).values())
    return bool(span - landed)"""

MERGES_BODY = """def merges(one, other):
    return bool(one & other)"""

MERGES_EQUAL = """def merges(one, other):
    return one == other"""

CARRY_LINE = "            carried = rule.kept(before, after)\n"

OUTDATE_BLOCK = ('            for thread in sorted(gone, key=lambda t: t["id"]):\n'
                 '                thread["state"] = "outdated"\n'
                 '                caught.pop(thread["id"], None)\n'
                 '                log.append(("outdated", thread["id"]))\n')

RAISE_BLOCK = ('                now = rule.touched(thread["span"], before, after)\n'
               '                if now and not caught.get(thread["id"], False):\n')

REOPEN_BLOCK = ('                    if thread["state"] == "answered":\n'
                '                        thread["state"] = "open"\n'
                '                        log.append(("reopen", thread["id"]))\n')

SKIP_BLOCK = ('                if thread["state"] not in ("open", "answered"):\n'
              '                    continue\n')

UNION_LINE = '            owner["span"] |= taken["span"]\n'
DRAG_BLOCK = ('            if taken["state"] == "open":\n'
              '                owner["state"] = "open"\n')
LOOP_TAIL = '            done.append((taken["id"], owner["id"]))'

SWAPS = [
    ("textbook-backtrace", "rule",
     "Build the surviving-line mapping with an ordinary longest common "
     "subsequence walk instead of reading it off the script the tool settled. "
     "Same number of moves every time; a different copy of a repeated line "
     "survives, so the span lands somewhere else.",
     KEPT_BODY, TEXTBOOK_KEPT),
    ("difflib-opcodes", "rule",
     "Take the mapping from the standard library's sequence matcher. It is not "
     "obliged to produce a shortest script and does not settle ties the way "
     "the tool does.",
     KEPT_BODY, DIFFLIB_KEPT),
    ("whole-span-must-be-touched", "rule",
     "Ask whether the change covers the span rather than whether it reaches "
     "any of it. A thread hangs off a stretch of code and the reviewer has to "
     "look again if the change got into part of it.",
     TOUCHED_BODY, TOUCHED_ALL),
    ("change-is-added-lines", "rule",
     "Treat a change as the lines the script added. A change reaches across "
     "the kept lines between its runs, so a line can come through a revision "
     "untouched and still be inside it.",
     TOUCHED_BODY, TOUCHED_ADDED),
    ("merge-on-equal-spans", "rule",
     "Merge two threads only when their spans are the same. Carrying squeezes "
     "spans that were opened apart into one another far more often than it "
     "makes them equal.",
     MERGES_BODY, MERGES_EQUAL),
    ("raise-every-revision", "board",
     "Ask the reviewer again every revision the thread spends caught in a "
     "change. It is raised when the change first reaches it; while it stays "
     "caught the reviewer has already been asked.",
     RAISE_BLOCK,
     '                now = rule.touched(thread["span"], before, after)\n'
     '                if now:\n'),
    ("answered-stays-answered", "board",
     "Leave an answered thread answered when the change comes back to it. The "
     "reply it is carrying was about code that has since moved.",
     REOPEN_BLOCK, '                    pass\n'),
    ("raise-resolved-threads", "board",
     "Raise a resolved thread along with the rest. It has been settled and "
     "nobody is waiting on it.",
     SKIP_BLOCK,
     '                if thread["state"] == "outdated":\n'
     '                    continue\n'),
    ("outdated-leaves-the-board", "board",
     "Drop a thread whose span has emptied instead of leaving it on the board "
     "outdated. The log still says what happened, and the table is shorter by "
     "exactly the threads a reviewer would go looking for.",
     OUTDATE_BLOCK,
     '            for thread in sorted(gone, key=lambda t: t["id"]):\n'
     '                caught.pop(thread["id"], None)\n'
     '                log.append(("outdated", thread["id"]))\n'
     '                threads.remove(thread)\n'),
    ("merge-in-one-pass", "board",
     "Merge the pairs that overlap and stop there. The union can reach a "
     "third thread that neither half reached on its own.",
     LOOP_TAIL, LOOP_TAIL + '\n            break'),
    ("merge-keeps-its-own-span", "board",
     "Let the older thread keep the span it had rather than taking the union. "
     "It is now the thread for both stretches of code.",
     UNION_LINE, '            pass\n'),
    ("open-does-not-drag", "board",
     "Let the merged thread keep the older thread's state. An unanswered "
     "question about that code is unanswered whichever thread carried it.",
     DRAG_BLOCK, '            pass\n'),
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
    counts = dict((item["name"], len(item["events"])) for item in scen.FIXED)
    board = '''import json

TRUTH = json.loads(%r)["fixed"]
COUNTS = %r


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, events):
        for name, body in sorted(TRUTH.items()):
            if COUNTS.get(name) == len(events):
                threads = [{"id": n, "state": st, "span": set(sp)}
                           for n, st, sp in body["threads"]]
                return threads, [tuple(e) for e in body["log"]]
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
