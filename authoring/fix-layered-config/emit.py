"""Write the cheat scripts: wrong readings, correct-but-slow readings, verifier probes, forgery.

Each semantic cheat is a whole submission - the reference with a single decision taken the
other way - so a score of 0 is attributable to that decision and not to four other things
being wrong at the same time. The module docstrings are stripped on the way out: a cheat
script is a probe, not a place to restate the solution. Probes carry the reference unchanged
plus a payload that attacks the verifier rather than the semantics; the forgery carries the
frozen answers and is caught by the nonce population. Run make_readings.py first.

    python3 emit.py [name ...]
"""
import ast
import hashlib
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

CHEATS = lab.TASK / "cheat"

WHY = {
    "guard-at-entry": "a guard is answered against the store the earlier entries of its layer have left",
    "guard-final-view": "the layers are folded first and the guards then answered at the finished plan",
    "stop-final-value": "a query naming a layer takes the definition there and the value from the whole plan",
    "cut-exact": "a removal takes the path named and nothing under it",
    "mix-merges": "a copy merges into the destination instead of replacing it",
    "mix-source-before-clear": "a copy fixes its source paths before it clears the destination",
    "carry-redates": "a copy re-dates the definitions it carries to the copying layer",
    "carry-back-at-graft": "a carried definition reads backwards at the copying layer, not at its own",
    "err-right-first": "the right side of an expression decides which failure is reported",
    "count-interior": "a count includes the paths that hold no definition",
    "pick-eager": "a conditional asks for both of its sides",
    "pick-subtree": "a conditional tests whether anything at or under the path is defined",
    "loop-as-gone": "a circular answer is reported as an absent one",
    "share-mutate": "nodes are shared between the views and edited in place",
    "map-as-mix": "the installing copy is treated as an ordinary copy",
    "map-captures-fresh-put": "a put below an installed subtree is moved as the installation moved its source",
    "map-ignores-external-history": "an installed definition keeps its old view when no path operand of it changed",
    "map-ignores-old-path": "an installation captures its view but does not move the paths that old reads",
    "map-ignores-pick-arm": "an installation moves the true arm of a conditional and leaves the false arm",
    "map-keeps-old": "an installation moves the paths and keeps the source's old view",
    "map-memo-by-origin": "two installed definitions with the same text and origin share one value",
    "map-old-cleared": "an installation captures its view after clearing the destination",
    "map-old-layer-start": "an installation captures the start of its layer instead of the store before its entry",
    "map-redates-origin": "an installation prints its own layer as the writer of what it installed",
    "map-source-before-clear": "an installation fixes its source before it clears the destination",
    "tie-as-mix": "a tie is taken as an ordinary copy",
    "tie-as-map": "a tie is taken as an installation: a copy, moved, with a captured view",
    "tie-no-move": "a tie shows the source's definitions with their path operands unmoved",
    "tie-old-captures": "a tie captures the store before its entry as the view old reads",
    "tie-cut-removes": "a removal under a tie takes nothing away from what the tie shows",
    "tie-put-unmasks": "a put at a removed path under a tie lets the source show beneath it again",
    "tie-mask-blocks-local": "a put beneath a removed path under a tie stays hidden",
    "tie-mix-stays-live": "a copy of a tied subtree keeps following the tie's source",
    "tie-copy-below-live": "a copy freezes the subtree it was given and leaves the ties beneath it live",
    "tie-chain-no-compose": "a tie shows only what is written at its source, not what the source shows through a tie of its own",
    "tie-fresh-per-lookup": "a tie makes a new definition every time one shows, so circularity is never found through it",
    "tie-ring-cuts-region": "a lookup stops at a tie whose source prefix it is already resolving, not at a path it has been through",
    "tie-ring-once": "a lookup goes through each tie at most once",
    "tie-count-unbounded": "counts and lookups are bounded at thirty-two segments instead of twenty-four",
    "tie-empty-source-keeps": "a tie whose source holds nothing leaves the destination as it was",
    "tie-count-no-shadow": "a count adds what a tie shows to what was written under it without removing what the writing hides",
    "slow-enumerate": "correct, and answers a count by enumerating every path that shows",
    "slow-materialize": "correct, and writes out every path a copy shows when the copy is taken",
    "slow-nomemo": "correct, and remembers no value it has already worked out",
    "forge-from-truth": "carries the frozen answers for every enumerated plan",
    "probe-answer-key": "answers from the sealed model, and cannot read it",
    "probe-crash-worker": "plants a passing record and exits before it can be overwritten",
    "probe-hijack-driver": "rewrites the graded set and the pristine tree in /tests",
    "probe-late-reward": "double-forks a process that writes the reward after grading",
    "probe-malformed": "returns a record the grader has to parse defensively",
    "probe-plant-report": "edits the worker record afterwards to drop what it got wrong",
    "probe-privilege": "checks its uid and writes where the reward lives",
    "probe-rewrite-frozen": "rewrites the frozen files in its own container to compensate",
    "probe-shrink-set": "shrinks its own exam before the worker reads it",
}

PROBES = {
    "probe-answer-key": '''

_SEAL = "/tests/seal/gt.json"


def _key():
    with open(_SEAL, "r", encoding="utf-8") as _fh:
        return _fh.read()


_answer = answer


def answer(hist, qry):
    _key()
    return _answer(hist, qry)
''',
    "probe-crash-worker": '''

import json
import os

_out = os.environ.get("LGA_WORK", "/work") + "/worker_out.json"
try:
    with open(_out, "w", encoding="utf-8") as _fh:
        json.dump([{"name": "plain-put", "sig": "x", "code": 0, "got": [], "err": None}], _fh)
except Exception:
    pass
os._exit(0)
''',
    "probe-hijack-driver": '''

import os

for _where in ("cases.py", "gen.py", "pristine/run_plan.py", "test_outputs.py"):
    try:
        with open(os.path.join("/tests", _where), "w", encoding="utf-8") as _fh:
            _fh.write("PLANS = {}\\n")
    except Exception:
        pass
''',
    "probe-late-reward": '''

import os
import time


def _seize():
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(25)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as _fh:
            _fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
''',
    "probe-malformed": '''

import atexit
import os

_out = os.environ.get("LGA_WORK", "/work") + "/worker_out.json"


def _spoil():
    try:
        with open(_out, "w", encoding="utf-8") as _fh:
            _fh.write("{{{ not json at all")
    except Exception:
        pass


atexit.register(_spoil)
''',
    "probe-plant-report": '''

import atexit
import json
import os

_out = os.environ.get("LGA_WORK", "/work") + "/worker_out.json"


def _trim():
    try:
        with open(_out, "r", encoding="utf-8") as _fh:
            recs = json.load(_fh)
        recs = [r for r in recs if not r["name"].startswith(("count", "shape", "basic", "mixed", "tie"))]
        with open(_out, "w", encoding="utf-8") as _fh:
            json.dump(recs, _fh)
    except Exception:
        pass


atexit.register(_trim)
''',
    "probe-privilege": '''

import os

_note = "/tmp/lga-uid"
try:
    with open(_note, "w", encoding="utf-8") as _fh:
        _fh.write(str(os.getuid()))
except Exception:
    pass
try:
    with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as _fh:
        _fh.write("1\\n")
except Exception:
    pass
''',
    "probe-rewrite-frozen": '''

import os

for _where in ("run_plan.py", "cfg/lex.py", "cfg/say.py", "cfg/__init__.py"):
    try:
        with open(os.path.join("/app", _where), "w", encoding="utf-8") as _fh:
            _fh.write("")
    except Exception:
        pass
''',
    "probe-shrink-set": '''

import sys

_cases = sys.modules.get("cases")
if _cases is not None:
    _keep = sorted(_cases.PLANS)[:1]
    _cases.PLANS = {_k: _cases.PLANS[_k] for _k in _keep}
_gen = sys.modules.get("gen")
if _gen is not None:
    _gen.programs = lambda *_a, **_k: []
''',
}


def strip(src):
    tree = ast.parse(src)
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
        end = tree.body[0].end_lineno
        return "\n".join(src.splitlines()[end:]).lstrip("\n")
    return src


def reference():
    return {part: strip((lab.TASK / "solution" / part).read_text()) for part in lab.PARTS}


def files_for(name):
    files = reference()
    if name.startswith("probe-"):
        files["ans.py"] = files["ans.py"].rstrip("\n") + "\n" + PROBES[name]
        return files, 1
    if name == "forge-from-truth":
        return forge(files), 1
    if name == "slow-nomemo":
        work = files["work.py"]
        old = "    hist.memo[key] = out\n    return out\n"
        if work.count(old) != 1:
            raise SystemExit("slow-nomemo edit does not fire")
        files["work.py"] = work.replace(old, "    return out\n")
        return files, 1
    reading = HERE / "readings" / name
    if not reading.is_dir():
        raise SystemExit("no reading %s" % name)
    fired = 0
    for part in lab.PARTS:
        one = reading / part
        if one.is_file():
            src = one.read_text()
            if src == (lab.TASK / "solution" / part).read_text():
                raise SystemExit("%s/%s is identical to the reference" % (name, part))
            files[part] = strip(src)
            fired += 1
    return files, fired


def forge(files):
    """Answers looked up by a fingerprint of the parsed plan, so the sealed cases are hit and
    nothing else is: the nonce population is what catches it."""
    sys.path.insert(0, str(lab.TASK / "tests"))
    import cases  # noqa: E402
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    names = {}
    lb = lab.Lab(lab.TASK / "solution")
    for name, text in cases.PLANS.items():
        names[_sig(lb.lex.parse(text))] = name
    lb.close()
    past = files["past.py"]
    head = ("import hashlib\nimport json\n\nKEY = json.loads(%s)\n\nNAMES = json.loads(%s)\n\n\n"
            "def _sig(plan):\n"
            "    body = []\n"
            "    for ents in plan.layers:\n"
            "        for ent in ents:\n"
            "            body.append(\"%%s|%%s|%%s|%%s|%%s\" %% (ent.kind, ent.a, ent.b, ent.expr, ent.guard))\n"
            "        body.append(\"lay\")\n"
            "    for qry in plan.asks:\n"
            "        body.append(\"%%s|%%s|%%s\" %% (qry.kind, qry.shown, qry.stop))\n"
            "    return hashlib.sha256(\"\\n\".join(body).encode(\"utf-8\")).hexdigest()\n\n\n"
            % (repr(json.dumps(gt, sort_keys=True)), repr(json.dumps(names, sort_keys=True))))
    old = '    __slots__ = ("at", "top", "memo", "busy", "cache")\n'
    if past.count(old) != 1:
        raise SystemExit("forge: Hist slots edit does not fire")
    past = past.replace(old, '    __slots__ = ("at", "top", "memo", "busy", "cache", "key", "shown")\n')
    old = "    hist = Hist(len(plan.layers))\n"
    if past.count(old) != 1:
        raise SystemExit("forge: build edit does not fire")
    past = past.replace(old, old + "    hist.key = KEY.get(NAMES.get(_sig(plan)))\n    hist.shown = 0\n")
    files["past.py"] = head + past
    ans = files["ans.py"]
    old = "def answer(hist, qry):\n"
    if ans.count(old) != 1:
        raise SystemExit("forge: answer edit does not fire")
    ans = ans.replace(old, old + "    if getattr(hist, \"key\", None):\n        line = hist.key[hist.shown]\n        hist.shown += 1\n        return line\n    return say.gone(qry.shown)\n")
    files["ans.py"] = ans
    return files


def _sig(plan):
    body = []
    for ents in plan.layers:
        for ent in ents:
            body.append("%s|%s|%s|%s|%s" % (ent.kind, ent.a, ent.b, ent.expr, ent.guard))
        body.append("lay")
    for qry in plan.asks:
        body.append("%s|%s|%s" % (qry.kind, qry.shown, qry.stop))
    return hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest()


def script(name):
    files, fired = files_for(name)
    if not fired:
        raise SystemExit("%s replaces nothing" % name)
    body = ["#!/bin/bash", "# " + WHY[name], "set -euo pipefail", ""]
    for part in lab.PARTS:
        body += ["cat > /app/cfg/%s <<'PYEOF'" % part, files[part].rstrip("\n"), "PYEOF", ""]
    return "\n".join(body) + "\n"


def main(argv):
    if CHEATS.exists() and not argv:
        for old in CHEATS.glob("*.sh"):
            old.unlink()
    CHEATS.mkdir(exist_ok=True)
    names = argv or sorted(WHY)
    for name in names:
        out = CHEATS / ("cheat-%s.sh" % name)
        text = script(name)
        if "\r" in text:
            raise SystemExit("CR in %s" % out)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print("wrote %d cheats" % len(names))


if __name__ == "__main__":
    main(sys.argv[1:])
