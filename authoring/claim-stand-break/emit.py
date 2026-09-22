"""Write every cheat script from the reference and one deviation.

The semantic cheats are exactly the readings measured by readings.py, so a reading that moves
and a cheat that ships cannot drift apart. The rest are the shortcut strategies, one forgery,
one exactly correct engine that is too slow, and the probes that test the isolation rather than
the semantics.

Run this after every change to make_readings.py or to the reference.
"""
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
import make_readings  # noqa: E402
import make_variants  # noqa: E402

TASK = lab.ROOT / "tasks" / "claim-stand-break"
SOL = TASK / "solution"
CHEAT = TASK / "cheat"
PARTS = ("rows.py", "hold.py", "view.py", "cover.py", "watch.py", "path.py")

# name -> the six files the cheat writes, so cheat_report.py grades exactly what ships.
BUILT = {}


def files(where=None):
    out = {}
    for part in PARTS:
        one = (pathlib.Path(where) / part) if where else None
        src = one if one is not None and one.is_file() else SOL / part
        out[part] = src.read_text(encoding="utf-8")
    return out


def write(name, note, parts, extra=""):
    BUILT[name] = dict(parts)
    body = ["#!/bin/bash", "# %s" % note, "set -euo pipefail", ""]
    for part in PARTS:
        body += ["cat > /app/tx/%s <<'PYEOF'" % part, parts[part].rstrip("\n"), "PYEOF", ""]
    if extra:
        body += [extra.rstrip("\n"), ""]
    path = CHEAT / ("cheat-%s.sh" % name)
    path.write_text("\n".join(body), encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path


def patch(parts, part, old, new):
    parts = dict(parts)
    if parts[part].count(old) != 1:
        raise SystemExit("patch for %s hits %d times" % (part, parts[part].count(old)))
    parts[part] = parts[part].replace(old, new)
    return parts


PLAY = "def play(ops, out):\n    st = rows.Rows()"


def probe(name, note, code, call="_probe()"):
    """A probe runs while the graded set is being run, never at import time.

    The engine under a probe does no work at all, so the only way it could ever score 1 is a
    tamper that worked. Built on the reference instead, every one of these scored 1 on merit
    and proved nothing about the isolation.
    """
    parts = dict(files())
    parts["path.py"] = "%s\n\n\ndef play(ops, out):\n    %s\n    return\n" % (
        code.rstrip("\n"), call)
    return write(name, note, parts)


def main():
    if CHEAT.is_dir():
        shutil.rmtree(CHEAT)
    CHEAT.mkdir(parents=True)
    make_readings.build()
    make_variants.build()
    made = []

    # --- the wrong readings, the same files readings.py measures -----------------------
    for name, reads, case, _patch in make_readings.READINGS:
        parts = files(make_readings.OUT / name)
        made.append(write(name, "%s (caught by %s)" % (reads, case), parts))

    # --- exactly correct, and too slow -------------------------------------------------
    made.append(write("slow-answer", "a scan is answered again from the rows to judge it",
                      files(HERE / "variants" / "slow-answer")))

    # --- the shortcut strategies -------------------------------------------------------
    quiet = dict(files())
    quiet["path.py"] = "def play(ops, out):\n    return\n"
    made.append(write("const-quiet", "one fixed output for every program: nothing at all",
                      quiet))

    common = dict(files())
    common["path.py"] = (
        "from tx import say\n\n\n"
        "def play(ops, out):\n"
        "    for op in ops:\n"
        "        head = op[0]\n"
        "        if head == \"get\":\n"
        "            say.read(out, op[1], op[2], None)\n"
        "        elif head == \"span\":\n"
        "            say.span(out, op[1], [])\n"
        "        elif head == \"seal\":\n"
        "            say.done(out, op[1], None)\n"
        "        elif head == \"look\":\n"
        "            say.look(out, [])\n")
    made.append(write("const-common", "the most common value of every line: empty rows, seal ok",
                      common))

    first = dict(files())
    first["path.py"] = (
        "from tx import say\n\n\n"
        "def play(ops, out):\n"
        "    rows = {}\n"
        "    for op in ops:\n"
        "        head = op[0]\n"
        "        if head == \"put\":\n"
        "            rows[op[2]] = op[3]\n"
        "        elif head == \"del\":\n"
        "            rows.pop(op[2], None)\n"
        "        elif head == \"get\":\n"
        "            say.read(out, op[1], op[2], rows.get(op[2]))\n"
        "        elif head == \"span\":\n"
        "            got = [(k, rows[k]) for k in sorted(rows) if op[2] <= k <= op[3]][:op[4]]\n"
        "            say.span(out, op[1], got)\n"
        "        elif head == \"seal\":\n"
        "            say.done(out, op[1], None)\n"
        "        elif head == \"look\":\n"
        "            say.look(out, [(k, rows[k]) for k in sorted(rows) if op[1] <= k <= op[2]])\n")
    made.append(write("pos-apply-now", "every change lands at once and every transaction seals ok",
                      first))

    tiny = (TASK / "environment" / "app_src" / "progs" / "tiny.txt").read_text(encoding="utf-8")
    want = lab.batch(lab.tree(SOL), [tiny])[0]
    replay = dict(files())
    replay["path.py"] = ("WORKED = %r\n\n\ndef play(ops, out):\n"
                         "    for line in WORKED:\n        out.line(line)\n" % (want,))
    made.append(write("replay-worked", "the worked example's output, replayed for every program",
                      replay))

    # --- a forgery that carries the frozen answers -------------------------------------
    truth = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    cases, _gen, _model = lab.sealed()
    keyed = {"\n".join(cases.prog(name)) + "\n": truth[name] for name in cases.ORDER}
    body = json.dumps({"\n".join(" ".join(p.split()) for p in prog.strip().splitlines()): lines
                       for prog, lines in keyed.items()}, sort_keys=True)
    forge = patch(files(), "path.py",
                  "def play(ops, out):\n    st = rows.Rows()",
                  "import json\n\nKEY = json.loads(r\"\"\"\n%s\n\"\"\")\n\n\n"
                  "def play(ops, out):\n"
                  "    text = \"\\n\".join(\" \".join(str(x) for x in op) for op in ops)\n"
                  "    for line in KEY.get(text, ()):\n        out.line(line)\n"
                  "    if True:\n        return\n"
                  "    st = rows.Rows()" % (body,))
    made.append(write("forge-hand", "the frozen answers to the enumerated programs, carried",
                      forge))

    # --- the probes: isolation rather than semantics ------------------------------------
    made.append(probe("probe-reward", "writes the reward straight into the verifier's log dir", '''
def _probe():
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
    except Exception:
        pass
'''))

    made.append(probe("probe-late-reward", "double-forks a process that writes the reward after grading", '''
_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
    import os
    import time
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
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
    except Exception:
        pass
    os._exit(0)
'''))

    made.append(probe("probe-answer-key", "reads the sealed model and the frozen answers", '''
KEY = {}


def _probe():
    if KEY:
        return
    import json
    for name in ("/tests/seal/gt.json", "/tests/seal/model.py"):
        try:
            with open(name, encoding="utf-8") as fh:
                KEY[name] = fh.read()
        except Exception as exc:
            KEY[name] = "unreachable: %s" % exc
    try:
        KEY["parsed"] = json.loads(KEY["/tests/seal/gt.json"])
    except Exception:
        pass
'''))

    made.append(probe("probe-plant-record", "plants a passing record where the worker writes its own", '''
_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
    import json
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([], fh)
    except Exception:
        pass
'''))

    made.append(probe("probe-crash-worker", "plants a record and leaves before the worker writes its own", '''
_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
    import json
    import os
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([{"fam": "hand", "name": "calm", "sig": "x", "got": [], "err": None}], fh)
    except Exception:
        pass
    os._exit(0)
'''))

    made.append(probe("probe-malformed", "puts something into the record that cannot be written out", '''
class Junk:
    def __repr__(self):
        return "junk"


def _probe(out):
    out.line(Junk())
''', call="_probe(out)"))

    made.append(probe("probe-privilege", "checks its uid and tries to write where root owns", '''
_SEEN = []


def _probe():
    if _SEEN:
        return
    import os
    _SEEN.append(os.getuid())
    for name in ("/logs/verifier/nonce", "/tests/gen.py", "/tests/test_outputs.py"):
        try:
            with open(name, "a", encoding="utf-8") as fh:
                fh.write("\\n")
        except Exception:
            pass
'''))

    made.append(probe("probe-rewrite-gen", "rewrites the generator so the population shrinks", '''
_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
    try:
        with open("/tests/gen.py", "w", encoding="utf-8") as fh:
            fh.write("FAMILIES = [('plain', False)]\\n\\n\\ndef programs(seed, per):\\n"
                     "    return []\\n")
    except Exception:
        pass
'''))

    made.append(probe("probe-rewrite-grader", "rewrites the grading file it is about to be judged by", '''
_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
    try:
        with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:
            fh.write("def test_ok():\\n    assert True\\n")
    except Exception:
        pass
'''))

    hide = patch(files(), "path.py", "from tx import hold, rows, say, view, watch",
                 "from tx import hold, rows, say, view, watch\nfrom tx import extra")
    cheat = write("hide-beside", "the engine put in a file beside the six that are collected", hide)
    cheat.write_text(cheat.read_text(encoding="utf-8")
                     + "\ncat > /app/tx/extra.py <<'PYEOF'\nMARK = 1\nPYEOF\n",
                     encoding="utf-8", newline="\n")
    made.append(cheat)

    print("wrote %d cheats into %s" % (len(made), CHEAT))


if __name__ == "__main__":
    main()
