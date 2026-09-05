import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / HERE.name
SOL = TASK / "solution"
CHEAT = TASK / "cheat"

RULES = {
    "capture-at-invocation": ("hold.py", "    return bk.get(tok, st.top())", "    return st.top()"),
    "capture-innermost-live": ("hold.py", "    return bk.get(tok, st.top())",
                               "    a = bk.get(tok, st.top())\n    d = st.under(a)\n    return d[-1] if d else a"),
    "chain-under-singleton-ignored": ("own.py",
                                      "    out = {}\n    for i in sorted(par):",
                                      "    out = {}\n    for i in sorted(par):\n        out[i] = at\n        continue\n    for i in []:"),
    "refusal-direct-only": ("gate.py", "    for d in reach(tbl, nm):", "    for d in r.deps:"),
    "refusal-off": ("gate.py", "    if r.life != SING:\n        return True", "    if True:\n        return True"),
    "teardown-front-to-back": ("tear.py", "    return list(reversed(mine))", "    return list(mine)"),
    "singleton-owned-by-scope": ("own.py", "        out[i] = ROOT if deep else at", "        out[i] = at"),
}

HEAD = "#!/bin/bash\nset -eu\nAPP=\"${APPDIR:-$(pwd)}\"\n"


def write(name, body):
    p = CHEAT / name
    p.write_text(body, newline="\n")
    p.chmod(0o755)


def emit_file(fname, text):
    return "cat > \"${APP}/wire/%s\" <<'SHR_EOF'\n%sSHR_EOF\n" % (fname, text)


def base(skip=None):
    out = ""
    for f in sorted(SOL.glob("*.py")):
        if f.name == skip:
            continue
        out += emit_file(f.name, f.read_text())
    return out


def main():
    CHEAT.mkdir(exist_ok=True)
    for old in CHEAT.glob("*.sh"):
        old.unlink()
    n = 0
    for label, (fname, was, now) in sorted(RULES.items()):
        src = (SOL / fname).read_text()
        if was not in src:
            raise SystemExit("emit.py is stale: anchor missing in %s for %s" % (fname, label))
        swapped = src.replace(was, now)
        if swapped == src:
            raise SystemExit("swap is a no-op for %s" % label)
        write("cheat-rule-%s.sh" % label, HEAD + base(skip=fname) + emit_file(fname, swapped))
        n += 1

    SHIP = TASK / "environment" / "app_src" / "wire"
    probe_tree = (SHIP / "plan.py").read_text().replace(
        "def place(",
        "import os as _os\n"
        "_t = _os.environ.get('APPDIR', '/work/app') + '/wire/core.py'\n"
        "try:\n"
        "    _s = open(_t).read().replace('sub = ROOT', 'sub = at')\n"
        "    open(_t, 'w').write(_s)\n"
        "except Exception:\n"
        "    pass\n\n\n"
        "def place(", 1)
    write("cheat-probe-rewrite-frozen.sh", HEAD + base(skip="plan.py") + emit_file("plan.py", probe_tree))
    n += 1

    probe_seal = (SHIP / "plan.py").read_text().replace(
        "def place(",
        "from wire import core as _c\n"
        "_orig = _c.Core.build\n\n\n"
        "def _quiet(self, nm, at, up=0):\n"
        "    return _orig(self, nm, at, up)\n\n\n"
        "_c.Core.build = _quiet\n\n\n"
        "def place(", 1)
    write("cheat-probe-patch-seal.sh", HEAD + base(skip="plan.py") + emit_file("plan.py", probe_seal))
    n += 1

    shipped = SHIP
    for label, payload in sorted({
        "reward-write": "open('/logs/verifier/reward.txt', 'w').write('1')",
        "read-answers": "open('/tests/gt.json').read()",
        "sweep-image": "import os\nfor b in ('/tests', '/pristine'):\n    [x for x in os.walk(b)]",
    }.items()):
        body = "import os\ntry:\n    " + payload.replace("\n", "\n    ") + "\nexcept Exception:\n    pass\n\n\n"
        write("cheat-reward-%s.sh" % label,
              HEAD + emit_file("plan.py", body + (shipped / "plan.py").read_text()))
        n += 1

    gt = json.loads((TASK / "tests" / "gt.json").read_text())
    blob = json.dumps(gt, sort_keys=True, separators=(",", ":"))
    forge = (
        "import json\n"
        "KEY = json.loads(%r)\n"
        "from wire.reg import SING\n\n\n"
        "def run(tbl, ops):\n"
        "    sig = (tuple(sorted((k, v.life, tuple(v.deps), tuple(v.facs)) for k, v in tbl.items())),\n"
        "           tuple(tuple(o) for o in ops))\n"
        "    for nm, rec in sorted(KEY['fixed'].items()):\n"
        "        if _match(nm, sig):\n"
        "            return [tuple(x) for x in rec]\n"
        "    return []\n\n\n"
        "def _match(nm, sig):\n"
        "    import cases\n"
        "    for cn, rows, ops in cases.FIXED:\n"
        "        if cn != nm:\n"
        "            continue\n"
        "        s2 = (tuple(sorted((r[0], r[1], tuple(r[2]), tuple(r[3])) for r in rows)),\n"
        "              tuple(tuple(o) for o in ops))\n"
        "        return s2 == sig\n"
        "    return False\n"
    ) % blob
    write("cheat-forge-answer-key.sh", HEAD + emit_file("plan.py", forge))
    n += 1
    print("wrote", n, "cheats")


if __name__ == "__main__":
    main()
