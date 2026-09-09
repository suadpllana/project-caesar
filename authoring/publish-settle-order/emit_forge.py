"""Write the forgery probe: a submission that already has the answers.

It carries the frozen traces for the enumerated programs and replays them, keyed on the program
it can see itself being handed, and does no work at all. The enumerated half of the grading
passes; the programs generated after the agent has finished do not exist in its table, so it
scores 0. That is the evidence that the verifier grades work rather than a claim about work.

    python3 authoring/publish-settle-order/emit_forge.py
"""
import hashlib
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TESTS = HERE.parents[1] / "tasks" / "publish-settle-order" / "tests"
sys.path.insert(0, str(TESTS))

import cases  # noqa: E402
import lab  # noqa: E402

ACTIONS = ("act", "open", "call", "rel")


def decls_of(lines):
    return sorted(ln for ln in lines if ln.split()[0] not in ACTIONS)


def acts_of(lines):
    return [ln for ln in lines if ln.split()[0] in ACTIONS]


def key(decls, acts):
    blob = "|".join(decls) + "#" + "|".join(acts)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


HEAD = '''import hashlib

TRUTH = %s

STATE = {"h": None, "acts": []}


def note(h, act):
    if STATE["h"] is not h:
        STATE["h"] = h
        STATE["acts"] = []
    STATE["acts"].append(act)


def _decls(h):
    out = []
    for name in h.units:
        r = h.units[name]
        out.append("unit " + name)
        for other, kind in r.needs:
            out.append("%%s %%s %%s" %% ("dep" if kind else "pre", name, other))
        for s, f in r.pubs:
            out.append("%%s %%s %%s" %% ("fall" if f else "pub", name, s))
        for b in r.boots:
            out.append("boot %%s %%s" %% (name, b))
    return out


def _cash(h, out):
    if len(h.units) > 64 or len(STATE["acts"]) > 64:
        return
    blob = "|".join(_decls(h)) + "#" + "|".join(STATE["acts"])
    got = TRUTH.get(hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16])
    if got is None:
        return
    del out[:]
    out.extend(got)


def bring(h, name, wide, out):
    note(h, ("act " if wide else "open ") + name)
    _cash(h, out)
'''

SITE = '''from link import walk


def reach(h, r, sym, out):
    walk.note(h, "call %s %s" % (r.name, sym))
    walk._cash(h, out)
'''

DROP = '''from link import walk


def let(h, name, out):
    walk.note(h, "rel " + name)
    walk._cash(h, out)
'''

PICK = '''def find(h, sym):
    return None
'''

WANT = '''def wanted(h, r):
    return True
'''


def main():
    truth = json.loads((TESTS / "seal" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    # The forger rebuilds the declaration block from the record table, so confirm that
    # round trip on every case before shipping a probe that would silently match nothing.
    lb = lab.Lab(lab.TASK / "solution")
    for name in cases.ORDER:
        lines = cases.ops(name)
        h = lb.tab.Host()
        acc = []
        for ln in lines:
            lb.ops.ex(h, tuple(ln.split()), acc)
        rebuilt = []
        for unit in h.units:
            rec = h.units[unit]
            rebuilt.append("unit " + unit)
            for other, kind in rec.needs:
                rebuilt.append("%s %s %s" % ("dep" if kind else "pre", unit, other))
            for s, f in rec.pubs:
                rebuilt.append("%s %s %s" % ("fall" if f else "pub", unit, s))
            for b in rec.boots:
                rebuilt.append("boot %s %s" % (unit, b))
        if sorted(rebuilt) != decls_of(lines):
            raise SystemExit("%s: the forger could not rebuild the declarations" % name)
        table[key(rebuilt, acts_of(lines))] = truth[name]
    lb.close()
    if len(table) != len(cases.ORDER):
        raise SystemExit("two cases collided on one key")

    body = ["#!/bin/bash",
            "# carries the frozen answers for the enumerated programs and replays them",
            "set -euo pipefail", ""]
    for part, src in (("walk.py", HEAD % json.dumps(table, sort_keys=True)),
                      ("pick.py", PICK), ("site.py", SITE), ("want.py", WANT),
                      ("drop.py", DROP)):
        body += ["cat > /app/link/%s <<'PYEOF'" % part, src.rstrip("\n"), "PYEOF", ""]
    out = lab.TASK / "cheat" / "cheat-forge-from-truth.sh"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(body) + "\n")
    out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print("wrote %s carrying %d frozen traces" % (out.name, len(table)))


if __name__ == "__main__":
    main()
