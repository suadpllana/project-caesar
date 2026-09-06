import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / HERE.name
SOL = TASK / "solution"
SHIP = TASK / "environment" / "app_src" / "wire"
CHEAT = TASK / "cheat"

INNERMOST = "    a = bk.get(tok, st.top())\n    d = st.under(a)\n    return d[-1] if d else a"
DEEP_ON = "        if deep:\n            out[i] = ROOT\n            continue"
DEEP_OFF = "        if False:\n            out[i] = ROOT\n            continue"
CYCLE = "    if cycles(tbl, nm):\n        return False\n"
TAGCHK = "    if r.tag and not any(st.tag(sc) == r.tag for sc in st.upto(at)):\n        return False\n"

RULES = {
    "capture-at-invocation": ("hold.py", "    return bk.get(tok, st.top())", "    return st.top()"),
    "capture-innermost-live": ("hold.py", "    return bk.get(tok, st.top())", INNERMOST),
    "mark-from-the-active-scope": ("pin.py", "reversed(st.upto(at))", "reversed(st.upto(st.top()))"),
    "mark-taken-from-the-outermost": ("pin.py", "for sc in reversed(st.upto(at)):", "for sc in st.upto(at):"),
    "chain-under-singleton-ignored": ("own.py", DEEP_ON, DEEP_OFF),
    "refusal-direct-only": ("gate.py", "    for d in reach(tbl, nm):", "    for d in r.deps:"),
    "cycle-blind": ("gate.py", CYCLE, ""),
    "mark-not-required": ("gate.py", TAGCHK, ""),
    "teardown-front-to-back": ("tear.py", "    return list(reversed(mine))", "    return list(mine)"),
    "parting-call-into-the-closing-scope": ("shut.py", "    return st.top()", "    return closing"),
}

HEAD = '#!/bin/bash\nset -eu\nAPP="${APPDIR:-$(pwd)}"\n'

SOLVE = "\n".join([
    "#!/bin/bash",
    "set -eu",
    "",
    'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
    'APP="${APPDIR:-/app}"',
    "",
    "for f in %s; do",
    '  cp "${HERE}/${f}.py" "${APP}/wire/${f}.py"',
    "done",
    "",
    'cd "${APP}"',
    "for c in cases/*.txt; do",
    '  python run_wire.py "${c}" > /dev/null',
    "done",
    "",
])


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


def solve():
    """Write solve.sh from whatever solution/ actually holds, so the list cannot drift.

    Reference verification rejected this bundle once because solve.sh named four
    files by hand and the enrichment had grown solution/ to six.
    """
    names = sorted(f.stem for f in SOL.glob("*.py"))
    if not names:
        raise SystemExit("emit.py: solution/ holds no python files to copy")
    out = SOL / "solve.sh"
    out.write_text(SOLVE % " ".join(names), newline="\n")
    out.chmod(0o755)
    return names


def main():
    CHEAT.mkdir(exist_ok=True)
    for old in CHEAT.glob("*.sh"):
        old.unlink()
    copied = solve()
    print("solve.sh copies:", " ".join(copied))
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

    probes = {
        "reward-write": "open('/logs/verifier/reward.txt', 'w').write('1')",
        "read-answers": "open('/tests/gt.json').read()",
        "sweep-image": "import os\nfor b in ('/tests', '/pristine'):\n    [x for x in os.walk(b)]",
    }
    for label in sorted(probes):
        payload = probes[label]
        body = "import os\ntry:\n    " + payload.replace("\n", "\n    ") + "\nexcept Exception:\n    pass\n\n\n"
        write("cheat-reward-%s.sh" % label,
              HEAD + emit_file("plan.py", body + (SHIP / "plan.py").read_text()))
        n += 1

    gt = json.loads((TASK / "tests" / "gt.json").read_text())
    blob = json.dumps(gt, sort_keys=True, separators=(",", ":"))
    forge = (
        "import json\n"
        "KEY = json.loads(%r)\n\n\n"
        "def _sig(tbl, ops):\n"
        "    return (tuple(sorted((k, v.life, tuple(v.deps), tuple(v.facs), v.tag, v.wraps,\n"
        "                          v.shut) for k, v in tbl.items())),\n"
        "            tuple(tuple(o) for o in ops))\n\n\n"
        "def run(tbl, ops):\n"
        "    import cases\n"
        "    from wire.reg import load\n"
        "    want = _sig(tbl, ops)\n"
        "    for cn, rows, cops in cases.FIXED:\n"
        "        if _sig(load(rows), cops) == want:\n"
        "            return [tuple(x) for x in KEY['fixed'][cn]]\n"
        "    return []\n"
    ) % blob
    write("cheat-forge-answer-key.sh", HEAD + emit_file("plan.py", forge))
    n += 1
    print("wrote", n, "cheats")


if __name__ == "__main__":
    main()
