#!/usr/bin/env python3
"""Write the forgery probe: a submission that already has the answers and does no geometry.

It carries the frozen lines for the thirty-nine enumerated programs and replays them, keyed on
the declarations it rebuilds from the tree and the per-frame edits it sees in the change log.
The enumerated half of the grading passes; the programs generated from a seed drawn after the
agent has finished share no key, so it scores 0. That is the evidence the verifier grades work
rather than a claim about work (CLAUDE.md, publish-settle-order: assert what the probe was
supposed to reproduce, not only what it scored).

The table is built by driving the environment's own spec and tree through the very fingerprint
functions the cheat runs, so the emit-time key and the runtime key cannot drift.

    python3 emit_forge.py
"""
import json
import stat
import sys

import lab

# The body shared verbatim between emit time and the shipped cheat: two fingerprints and a
# tuple->list normaliser, so a key computed here and a key computed in the container are equal.
SHARED = '''
def _flags(b):
    fl = []
    if b.pin is not None:
        fl.append("pin=%d" % b.pin)
    if b.shut:
        fl.append("shut")
    if b.lift:
        fl.append("lift")
    if b.live:
        fl.append("live")
    return tuple(sorted(fl))


def _decls(v):
    rows = tuple(sorted((bid, ("-" if b.par is None else b.par.id), b.own, _flags(b))
                        for bid, b in v.box.items()))
    return ("view", v.vh, "at", v.s, rows)


def _sig(log):
    return tuple(("to", arg) if kind == "to" else (kind, b.id) for kind, b, arg in log)


def _norm(x):
    return [_norm(y) for y in x] if isinstance(x, tuple) else x
'''

RUNTIME = SHARED + '''
import json

GT = json.loads(_GT)
INDEX = json.loads(_INDEX)
STATE = {"decls": None, "cum": ()}


def start(v):
    STATE["decls"] = None
    STATE["cum"] = ()


def before(v):
    if STATE["decls"] is None:
        STATE["decls"] = _decls(v)


def after(v):
    STATE["cum"] = STATE["cum"] + (_sig(v.log),)
    where = INDEX.get(json.dumps(_norm((STATE["decls"], STATE["cum"]))))
    if where is None:
        return max(v.s, 0), "none"
    case, idx = where
    part = GT[case][idx].split(" ", 2)
    return int(part[1]), part[2]
'''


def build_index(truth):
    """Map each declaration+edit prefix to the (case, frame) whose gt.json line answers it."""
    cases, _gen, _model = lab.sealed()
    here = lab.tree(None)
    lab.inproc(here)
    from view import spec, tree

    ns = {}
    exec(SHARED, ns)
    decls_of, sig_of, norm = ns["_decls"], ns["_sig"], ns["_norm"]

    index = {}
    for name in cases.ORDER:
        prog = spec.parse("\n".join(cases.prog(name)) + "\n")
        v = tree.View(prog)
        decls = decls_of(v)
        cum = ()
        for n, ops in enumerate(prog.frames):
            for op in ops:
                v.apply(op)
            cum = cum + (sig_of(v.log),)
            del v.log[:]
            key = json.dumps(norm((decls, cum)))
            if index.get(key, [name, n]) != [name, n]:
                raise SystemExit("two enumerated prefixes collide at %s" % name)
            index[key] = [name, n]
    return index


def main():
    truth = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    index = build_index(truth)
    # The cheat carries gt.json verbatim - it is handed every answer - and replays the line the
    # prefix it can see maps to. forgecheck looks for exactly this: a probe built from the truth.
    body = ("_GT = " + repr(json.dumps(truth, sort_keys=True)) + "\n"
            + "_INDEX = " + repr(json.dumps(index)) + "\n") + RUNTIME
    ns = {}
    exec(compile(body, "<forge>", "exec"), ns)
    assert ns["GT"] == truth and ns["INDEX"] == index, "forge did not round-trip"

    parts = {"lay.py": "\n", "stick.py": "\n", "pick.py": "\n", "hold.py": body}
    sh = ["#!/bin/bash",
          "# carries the frozen lines for the enumerated programs and replays them, no geometry",
          "set -euo pipefail", ""]
    for part, text in parts.items():
        sh += ["cat > /app/view/%s <<'PYEOF'" % part, text.rstrip("\n"), "PYEOF", ""]
    out = lab.TASK / "cheat" / "cheat-forge-from-truth.sh"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sh) + "\n")
    out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print("wrote %s carrying gt.json and %d prefixes" % (out.name, len(index)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
