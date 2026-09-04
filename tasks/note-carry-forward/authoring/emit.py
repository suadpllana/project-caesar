"""Generate cheat/ from the reference. Never hand-edit what this writes.

Every rule cheat is the whole reference with exactly one decision made the way
a solver who missed one thing would make it, produced by an anchored swap that
has to match or this refuses to write. A swap that silently matches nothing
ships the reference and proves nothing.
"""
import json
import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
BOARD = (TASK / "solution" / "board.py").read_text()
RULE = (TASK / "solution" / "rule.py").read_text()

DIFFLIB_KEEP = '''            keep = {}
            _sm = difflib.SequenceMatcher(None, before, after, autojunk=False)
            for _tag, _i1, _i2, _j1, _j2 in _sm.get_opcodes():
                if _tag == "equal":
                    for _d in range(_i2 - _i1):
                        keep[_i1 + _d] = _j1 + _d
'''

TEXTBOOK_KEEP = '''            _n, _m = len(before), len(after)
            _L = [[0] * (_m + 1) for _ in range(_n + 1)]
            for _i in range(_n - 1, -1, -1):
                for _j in range(_m - 1, -1, -1):
                    if before[_i] == after[_j]:
                        _L[_i][_j] = _L[_i + 1][_j + 1] + 1
                    else:
                        _L[_i][_j] = max(_L[_i + 1][_j], _L[_i][_j + 1])
            keep = {}
            _i = _j = 0
            while _i < _n and _j < _m:
                if before[_i] == after[_j] and _L[_i][_j] == _L[_i + 1][_j + 1] + 1:
                    keep[_i] = _j
                    _i += 1
                    _j += 1
                elif _L[_i + 1][_j] >= _L[_i][_j + 1]:
                    _i += 1
                else:
                    _j += 1
'''

KEEP_LINE = '            keep = rule.kept(pin.reading(before, after, pin.script(before, after)))\n'

ORIGIN_BUILD = '''    def build(self, opens):
        head = self.store.count() - 1
        live = []
        log = []
        for at, nid, line in sorted(opens, key=lambda o: o[1]):
            here = self.store.at(at)
            there = self.store.at(head)
            keep = rule.kept(pin.reading(here, there, pin.script(here, there)))
            if line in keep:
                live.append({"id": nid, "line": keep[line]})
            else:
                log.append(("retire", nid))
        if head > 0:
            spans = grp.spans(self.store.at(head - 1), self.store.at(head))
            for note in live:
                if rule.raised(note["line"], spans):
                    log.append(("raise", note["id"]))
        self._open(live, log, [])
        live.sort(key=lambda n: n["id"])
        return live, log
'''

SWAPS = [
    ("origin-to-head", "board",
     "Rebuild each note by asking the engine for the script from the revision "
     "it was opened at straight to the head. Stateless, one engine call a note "
     "rather than one a revision, and the shape the shipped tree already has. "
     "The pinned script does not compose, so it resurrects notes whose line "
     "died revisions ago and whose text was typed again later.",
     BOARD[BOARD.index("    def build(self, opens):"):BOARD.index("    def _open(")],
     ORIGIN_BUILD),
    ("textbook-backtrace", "board",
     "Rebuild the surviving-line mapping with an ordinary longest common "
     "subsequence backtrace instead of reading it off the walk the pinned "
     "engine produced. Same number of moves every time; a different copy of a "
     "repeated line survives.",
     KEEP_LINE, TEXTBOOK_KEEP),
    ("difflib-opcodes", "board",
     "Take the mapping from the standard library's sequence matcher, which is "
     "right there and returns equal blocks directly. It is not obliged to "
     "produce a shortest script and does not settle ties the way the engine "
     "does.",
     KEEP_LINE, DIFFLIB_KEEP),
    ("raise-added-lines-only", "board",
     "Raise a note only where the script added the line under it. A change "
     "absorbs the kept lines sitting between its runs, so a line can survive a "
     "revision untouched and still be part of the change.",
     '                if rule.raised(note["line"], spans):\n',
     '                if rule.raised(note["line"], spans) \\\n'
     '                        and note["line"] not in keep.values():\n'),
    ("absorb-newer-wins", "board",
     "Let the note that arrived last keep the line. The rule gives it to the "
     "older one.",
     '        for note in sorted(live, key=lambda n: n["id"]):\n'
     '            owner = seen.get(note["line"])\n',
     '        for note in sorted(live, key=lambda n: -n["id"]):\n'
     '            owner = seen.get(note["line"])\n'),
    ("never-absorb", "board",
     "Leave two notes sitting on one line. Nothing in a single revision makes "
     "that visible, and the log never mentions it.",
     '            else:\n                taken.append((note["id"], owner))\n',
     '            else:\n                held.append(note)\n'),
    ("retire-without-saying", "board",
     "Drop a note whose line is gone without logging it. The table at the head "
     "comes out right and the log is short.",
     '            for nid in sorted(lost):\n                log.append(("retire", nid))\n',
     '            for nid in sorted(lost):\n                pass\n'),
    ("raise-before-retire", "board",
     "Log the raises before the retirements. Both sets are right and the table "
     "at the head is right; only the order of the log moves, which is the one "
     "thing two correct boards must not be free to disagree about.",
     '            for nid in sorted(lost):\n                log.append(("retire", nid))\n'
     '            live[:] = held\n'
     '            for note in sorted(live, key=lambda n: n["id"]):\n'
     '                if rule.raised(note["line"], spans):\n'
     '                    log.append(("raise", note["id"]))\n',
     '            live[:] = held\n'
     '            for note in sorted(live, key=lambda n: n["id"]):\n'
     '                if rule.raised(note["line"], spans):\n'
     '                    log.append(("raise", note["id"]))\n'
     '            for nid in sorted(lost):\n                log.append(("retire", nid))\n'),
    ("open-before-carrying", "board",
     "Admit the notes opened at a revision before carrying the ones already "
     "there, so a note opened at that revision is carried through the script "
     "that produced it.",
     '            self._open(live, log, waiting.get(step, []))\n',
     '            pass\n'),
]


def emit_one(name, which, why, old, new):
    board, rule = BOARD, RULE
    if which == "board":
        if old not in board:
            raise SystemExit("anchor did not match for %s" % name)
        if old == new:
            raise SystemExit("swap is a no-op for %s" % name)
        board = board.replace(old, new, 1)
        if name in ("difflib-opcodes",):
            board = "import difflib\n" + board
        if name == "absorb-newer-wins":
            board = board.replace(
                '        for nid, owner in sorted(taken):\n'
                '            log.append(("absorb", owner, nid))\n',
                '        for nid, owner in sorted(taken):\n'
                '            log.append(("absorb", nid, owner))\n', 1)
        if name == "open-before-carrying":
            board = board.replace(
                '            keep = rule.kept(',
                '            self._open(live, log, waiting.get(step, []))\n'
                '            keep = rule.kept(', 1)
    else:
        if old not in rule:
            raise SystemExit("anchor did not match for %s" % name)
        rule = rule.replace(old, new, 1)
    body = ['#!/bin/bash', '# ' + why.replace('\n', '\n# '), 'set -euo pipefail',
            'APP_DIR="${APP_DIR:-/app}"',
            "cat > \"${APP_DIR}/note/board.py\" <<'ENDBOARD'", board.rstrip('\n'), 'ENDBOARD',
            "cat > \"${APP_DIR}/note/rule.py\" <<'ENDRULE'", rule.rstrip('\n'), 'ENDRULE']
    path = TASK / "cheat" / ("cheat-rule-%s.sh" % name)
    with open(path, "w", newline="\n") as fh:
        fh.write("\n".join(body) + "\n")
    path.chmod(0o755)
    return path.name


def emit_answer_key():
    """The probe that makes forgecheck worth running: an adversary holding the
    verifier's own ground truth. Right on every hand-written stream and wrong
    on the generated ones, which are built from a seed chosen after the
    submission was written."""
    gt = json.loads((TASK / "tests" / "gt.json").read_text())
    blob = json.dumps(gt, sort_keys=True, separators=(",", ":"))
    board = '''import json

TRUTH = json.loads(%r)["fixed"]


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, opens):
        want = None
        for name, body in TRUTH.items():
            if self._fits(name, body, opens):
                want = body
                break
        if want is None:
            return [], []
        live = [{"id": n, "line": l} for n, l in want["notes"]]
        return live, [tuple(e) for e in want["log"]]

    def _fits(self, name, body, opens):
        return len(opens) == self._opens_for(name)

    def _opens_for(self, name):
        return COUNTS.get(name, -1)


COUNTS = %r
''' % (blob, {})
    counts = {}
    sys.path.insert(0, str(TASK / "tests"))
    import scen
    for item in scen.FIXED:
        counts[item["name"]] = len(item["opens"])
    board = board.replace("COUNTS = {}", "COUNTS = %r" % counts)
    body = ['#!/bin/bash',
            '# Deliberate cheating attempt. Holds tests/gt.json and returns the',
            '# recorded answer for whichever hand-written stream it thinks it is',
            '# looking at. Right on those and wrong on the generated block, which',
            '# is built inside the verifier from a seed chosen after this was',
            '# written. Generated-after-the-fact input beats any answer key.',
            'set -euo pipefail', 'APP_DIR="${APP_DIR:-/app}"',
            "cat > \"${APP_DIR}/note/board.py\" <<'ENDBOARD'", board.rstrip('\n'), 'ENDBOARD']
    path = TASK / "cheat" / "cheat-forge-answer-key.sh"
    with open(path, "w", newline="\n") as fh:
        fh.write("\n".join(body) + "\n")
    path.chmod(0o755)
    return path.name


def main():
    made = []
    for name, which, why, old, new in SWAPS:
        made.append(emit_one(name, which, why, old, new))
    made.append(emit_answer_key())
    print("wrote %d cheats:" % len(made))
    for n in sorted(made):
        print("   ", n)


if __name__ == "__main__":
    main()
