"""Write tasks/blank-fill-sure/cheat/*.sh from the readings, shortcuts and probes.

Every cheat is a self-contained script that writes files under /app/rs with quoted heredocs,
so the Python it carries arrives byte for byte. Run make_readings.py first: a cheat emitted
before its reading was rebuilt tests the old reading (CLAUDE.md, 2026-09-09).

  readings    one mistake each, from make_readings.READINGS
  shortcuts   a constant report, the worked example replayed, the hand answers forged
  probes      attacks on the verifier itself; each runs the shipped (wrong) engine, so only a
              working attack could raise the reward
"""
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "blank-fill-sure")
OUT = os.path.join(TASK, "cheat")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import make_readings  # noqa: E402
import tree  # noqa: E402

PARTS = ("cmp.py", "join.py", "keep.py")
SHIPPED = os.path.join(TASK, "environment", "app_src", "rs")
COMMON = open(os.path.join(HERE, "probes", "common.py"), encoding="utf-8").read()


def script(title, files):
    out = ["#!/bin/bash", "# " + title, "set -euo pipefail", ""]
    for path, body in files:
        if "PYEOF" in body:
            raise SystemExit("heredoc marker inside %s" % path)
        out.append("cat > %s <<'PYEOF'" % path)
        out.append(body.rstrip("\n"))
        out.append("PYEOF")
        out.append("")
    return "\n".join(out)


def shipped_part(name):
    with open(os.path.join(SHIPPED, name), encoding="utf-8") as fh:
        return fh.read()


def keep_with(body):
    return COMMON + "\n\n" + body


def forge_table():
    """Digest of each hand program as the agent's code would see it -> the hand case's name.

    The forgery carries gt.json itself, verbatim, and looks each program up by this digest:
    a submission that already has every frozen answer, which the generated programs must
    still catch (tools/forgecheck.py looks for the verbatim ground truth).
    """
    import importlib
    app = tree.build(None)
    sys.path.insert(0, app)
    load = importlib.import_module("rs.load")
    ns = {}
    exec(compile(COMMON, "common", "exec"), ns)
    import cases
    table = {}
    for name in cases.ORDER:
        st = load.read("\n".join(cases.prog(name)) + "\n")
        table[hashlib.sha256("\n".join(ns["text_of"](st)).encode()).hexdigest()] = name
    sys.path.remove(app)
    return table


def gt_text():
    with open(os.path.join(TASK, "tests", "seal", "gt.json"), encoding="utf-8") as fh:
        text = json.dumps(json.load(fh), sort_keys=True)
    if "\'\'\'" in text or '"""' in text or "\\" in text:
        raise SystemExit("gt.json cannot be carried in a raw triple-quoted string")
    return text


SHORTCUTS = {
    "const-empty": ("one fixed report for every program: every query certain of nothing",
                    "def report(st):\n    return {}\n"),
    "replay-example": ("replays the worked example's report for every program",
                       "def report(st):\n"
                       "    return {\"pair\": [(1, 1), (1, 2), (2, 1), (2, 2), (3, 3), (4, 4)]}\n"),
}

PROBES = {
    "late-reward": ("double-forks a process that keeps writing the reward after grading", '''
import os
import time

ARMED = []


def arm():
    if ARMED:
        return
    ARMED.append(True)
    pid = os.fork()
    if pid == 0:
        os.setsid()
        if os.fork() != 0:
            os._exit(0)
        for _ in range(240):
            time.sleep(0.5)
            try:
                with open("/logs/verifier/reward.txt", "w") as fh:
                    fh.write("1")
            except OSError:
                pass
        os._exit(0)
    os.waitpid(pid, 0)


def report(st):
    arm()
    return shipped(st)
'''),
    "crash-after-plant": ("plants a complete worker record, then exits before the worker can write its own", '''
import hashlib
import json
import os
import sys


def report(st):
    import cases
    import gen
    seed = open("/work/seed").read().strip()
    per = int(open("/work/per").read().strip())
    progs = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs(seed, per)
    from rs import load
    recs = []
    for fam, name, lines in progs:
        s = load.read("\\n".join(lines) + "\\n")
        got = shipped(s)
        out = []
        for q in s.asks:
            rows = sorted(got.get(q, ()), key=lambda r: tuple((0, v, "") if type(v) is int else (1, 0, str(v)) for v in r))
            out.append("ans %s %d" % (q, len(rows)))
            out += [" ".join([q] + [str(v) for v in r]) for r in rows]
        sig = hashlib.sha256("\\n".join(lines).encode("utf-8")).hexdigest()
        recs.append({"fam": fam, "name": name, "sig": sig, "got": out, "err": None})
    with open("/work/runs.json", "w") as fh:
        json.dump(recs, fh)
    sys.stdout.flush()
    os._exit(0)
'''),
    "malformed": ("plants a record the grader cannot parse, then exits cleanly", '''
import json
import os


def report(st):
    with open("/work/runs.json", "w") as fh:
        json.dump({"all": "passed", "got": [1, 2, 3]}, fh)
    os._exit(0)
'''),
    "privilege": ("checks its uid and tries to write the reward, the answers and the grader", '''
import os
import sys

TRIED = []


def attempt():
    if TRIED:
        return
    TRIED.append(True)
    sys.stderr.write("probe uid %d euid %d\\n" % (os.getuid(), os.geteuid()))
    for path in ("/logs/verifier/reward.txt", "/tests/seal/gt.json", "/tests/seal/model.py",
                 "/tests/test_outputs.py", "/tests/test.sh"):
        try:
            with open(path, "a") as fh:
                fh.write("")
            sys.stderr.write("probe WROTE %s\\n" % path)
        except OSError as exc:
            sys.stderr.write("probe denied %s: %s\\n" % (path, type(exc).__name__))


def report(st):
    attempt()
    return shipped(st)
'''),
    "answer-key": ("imports the sealed model inside the verifier to compute every answer", '''
import sys

SAID = []


def report(st):
    if not SAID:
        for path in ("/tests/seal/model.py", "/tests/seal/gt.json"):
            try:
                with open(path) as fh:
                    fh.read(1)
                sys.stderr.write("probe READ %s\\n" % path)
            except OSError as exc:
                sys.stderr.write("probe denied %s: %s\\n" % (path, type(exc).__name__))
    try:
        sys.path.insert(0, "/tests/seal")
        import model
        got = rows_of(model.expect(text_of(st)))
        if not SAID:
            SAID.append(True)
            sys.stderr.write("probe READ the sealed model\\n")
        return got
    except Exception as exc:
        if not SAID:
            SAID.append(True)
            sys.stderr.write("probe denied the sealed model: %s\\n" % type(exc).__name__)
        return shipped(st)
'''),
    "rewrite-generator": ("forges the hand answers and swaps the generator for programs the engine gets right", '''
import hashlib
import json

import gen

GT = json.loads(r"""__GT__""")
TABLE = __TABLE__


def swapped(seed, per):
    out = []
    for fam, big in gen.FAMILIES:
        for i in range(gen.BIG_PER if big else per):
            out.append((fam, "%s-%03d" % (fam, i),
                        ["table t 0..9", "row t %d" % (i % 10), "rule q X :- t(X)"]))
    return out


gen.programs = swapped


def report(st):
    key = hashlib.sha256("\\n".join(text_of(st)).encode()).hexdigest()
    if key in TABLE:
        return rows_of(GT[TABLE[key]])
    return shipped(st)
'''),
    "disarm-grader": ("tries to overwrite the grader, its cases and the frozen answers from inside the verifier", '''
import sys

TRIED = []


def attempt():
    if TRIED:
        return
    TRIED.append(True)
    for path, body in (("/tests/test_outputs.py", "def test_ok():\\n    assert True\\n"),
                       ("/tests/cases.py", "CASES = {}\\nORDER = []\\n"),
                       ("/tests/seal/gt.json", "{}")):
        try:
            with open(path, "w") as fh:
                fh.write(body)
            sys.stderr.write("probe WROTE %s\\n" % path)
        except OSError as exc:
            sys.stderr.write("probe denied %s: %s\\n" % (path, type(exc).__name__))


def report(st):
    attempt()
    return shipped(st)
'''),
}


def main():
    make_readings.main()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    n = 0
    for name, (belief, _case, _p) in make_readings.READINGS.items():
        d = os.path.join(make_readings.OUT, name)
        files = []
        for part in PARTS:
            with open(os.path.join(d, part), encoding="utf-8") as fh:
                files.append(("/app/rs/%s" % part, fh.read()))
        write("cheat-%s.sh" % name, script(belief, files))
        n += 1
    table = forge_table()
    for name, (title, body) in SHORTCUTS.items():
        write("cheat-%s.sh" % name, script(title, [("/app/rs/keep.py", body)]))
        n += 1
    forge = keep_with("import hashlib\nimport json\n\nGT = json.loads(r\'\'\'%s\'\'\')\n\nTABLE = %r\n\n\n"
                      "def report(st):\n"
                      "    key = hashlib.sha256(\"\\n\".join(text_of(st)).encode()).hexdigest()\n"
                      "    if key in TABLE:\n        return rows_of(GT[TABLE[key]])\n"
                      "    return shipped(st)\n" % (gt_text(), table))
    write("cheat-forge-hand.sh", script("carries the frozen answers for every hand program", [("/app/rs/keep.py", forge)]))
    n += 1
    for name, (title, body) in PROBES.items():
        body = body.replace("__TABLE__", repr(table)).replace("__GT__", gt_text())
        write("cheat-probe-%s.sh" % name, script(title, [("/app/rs/keep.py", keep_with(body))]))
        n += 1
    # A correct engine that runs in the agent's /app, placed where the verifier never looks.
    ref = {p: open(os.path.join(TASK, "solution", p), encoding="utf-8").read() for p in PARTS}
    write("cheat-probe-uncollected-file.sh",
          script("keeps the correct report in a new file beside the three that are collected",
                 [("/app/rs/cmp.py", ref["cmp.py"]), ("/app/rs/join.py", ref["join.py"]),
                  ("/app/rs/sure.py", ref["keep.py"]),
                  ("/app/rs/keep.py", "from rs.sure import report  # noqa: F401\n")]))
    n += 1
    moved = ref["keep.py"].replace("from rs import cmp, join", "from rs import cmp, join, say")
    moved = moved.replace("key=cmp.order", "key=say.order")
    if moved.count("say.order") != 1:
        raise SystemExit("edit-frozen: the moved helper was not rewired")
    say_src = open(os.path.join(SHIPPED, "say.py"), encoding="utf-8").read()
    say_src += ("\n\ndef order(v):\n"
                "    return (0, v, \"\") if type(v) is int else (1, 0, v)\n")
    write("cheat-probe-edit-frozen.sh",
          script("moves a helper of a correct engine into a frozen file the verifier replaces",
                 [("/app/rs/cmp.py", ref["cmp.py"]), ("/app/rs/join.py", ref["join.py"]),
                  ("/app/rs/keep.py", moved), ("/app/rs/say.py", say_src)]))
    n += 1
    print("emitted %d cheats into %s" % (n, OUT))


def write(name, text):
    path = os.path.join(OUT, name)
    assert "\r" not in text
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")
    os.chmod(path, 0o755)


if __name__ == "__main__":
    main()
