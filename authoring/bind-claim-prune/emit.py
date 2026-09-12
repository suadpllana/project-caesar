"""Write every cheat script from the engines that already exist.

A cheat is a whole submission, so each script drops all six files: the wrong readings are the
reference with one rule read the other way, the slow ones are the reference with one structure
replaced by the method the rule literally describes, the forgery is the shipped engine with the
frozen answers bolted on, and the probes are the SHIPPED engine with a payload that runs while
the graded set is running.

Two things here were learned the hard way and are not style. A probe is built on the shipped
engine rather than the reference, because a probe built on a working engine scores 1 the moment
its attack is refused - which is a report about nothing. Built on an engine that cannot pass on
its own, a 1 can only mean the tamper landed, and a 0 next to the refusal written into the probe
log is the evidence that the isolation held. And a payload fires from inside the call the runner
makes per program, not at import time, because an attack at import happens before the runner has
armed anything.

Run this AFTER make_readings.py, never before: a cheat emitted from a stale reading directory
tests a rule that has since been repaired, and the two reports then disagree with each other
rather than with the task.

    python authoring/bind-claim-prune/emit.py
"""
import inspect
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "bind-claim-prune"
REF = TASK / "solution"
SHIPPED = TASK / "environment" / "app_src" / "bind"
OUT = TASK / "cheat"
PARTS = ("hold.py", "want.py", "pull.py", "place.py", "prune.py", "wire.py")

WHY = {
    "claim-sticks": "a claim key never changes hands (caught by shift-key)",
    "claim-never": "a held claim key does not drop the part (caught by claim-drop)",
    "firm-never": "a key held off the input list is displaceable too (caught by shift-firm)",
    "give-stays": "a displaced part keeps the gives it put in (caught by shift-key)",
    "use-stays": "a displaced part keeps the uses it put in (caught by shift-use-gone)",
    "one-give": "one strong give per name, so nothing to fall back to (caught by shift-rebind)",
    "dup-replaces": "a second strong give replaces the first (caught by dup-report)",
    "weak-settles": "a weak give settles a name (caught by weak-give)",
    "spare-quiet": "a spare does not make a name wanted (caught by spare-want)",
    "weak-wants": "a weak use makes a name wanted (caught by weak-use-quiet)",
    "take-oldest": "the member for the name wanted first, not the first member (take-order)",
    "take-onward": "the scan carries on past the member just taken (caught by take-restart)",
    "rescan-back": "a name wanted again is carried back to a bundle behind it (shift-earlier)",
    "group-once": "a group of bundles is scanned once (caught by group-pass)",
    "weak-reaches": "the prune follows weak uses (caught by weak-reach)",
    "hold-quiet": "a held part is not a root (caught by prune-hold)",
    "spare-first": "a spare is placed at the first size spared (caught by spare-size)",
    "spare-late": "a size tie goes to the last unit that spared it (caught by spare-size)",
    "at-preprune": "a name whose part the prune dropped still reports it (prune-drop)",
    "img-all-spares": "the image counts every placed name (caught by spare-reach)",
}

SLOW = {
    "rescan": "exactly correct, and the member scan is restarted from the first member",
    "rebuild": "exactly correct, and the wanted set is re-read off the kept parts",
    "perpart": "exactly correct, and reachability is asked once per part",
}

PROBE_HEAD = '''
import os as _os
import sys as _sys

_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    try:
        _go()
    except Exception as exc:
        _note("%s: %s" % (type(exc).__name__, exc))


def _note(text):
    try:
        with open("/work/probe.log", "a", encoding="utf-8") as fh:
            fh.write(text + "\\n")
    except OSError:
        pass
'''

PROBES = {
    "probe-answer-key": ("reads the sealed model and answers from it", '''
def _go():
    _sys.path.insert(0, "/tests/seal")
    import model
    _note("model imported from %s" % model.__file__)
'''),
    "probe-late-reward": ("double-forks a process that writes the reward after grading", '''
def _go():
    if _os.fork():
        return
    _os.setsid()
    if _os.fork():
        _os._exit(0)
    import time
    time.sleep(40)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
        _note("late write landed")
    except OSError as exc:
        _note("late write refused: %s" % exc)
    _os._exit(0)
'''),
    "probe-plant-report": ("writes a passing worker record and does no work", '''
def _go():
    import json
    _sys.path.insert(0, "/tests")
    import cases
    truth = json.loads(open("/tests/seal/gt.json", encoding="utf-8").read())
    recs = [{"fam": "hand", "name": n, "sig": "x", "got": truth[n], "err": None}
            for n in cases.ORDER]
    with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
        fh.write(json.dumps(recs))
    _note("report planted")
'''),
    "probe-crash-worker": ("plants a report and exits the worker clean before it is written", '''
def _go():
    import json
    with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
        fh.write(json.dumps([{"fam": "hand", "name": "plain-link", "sig": "x",
                              "got": ["ok"], "err": None}]))
    _note("planted then exiting clean")
    _os._exit(0)
'''),
    "probe-malformed": ("leaves the worker record unparseable and exits clean", '''
def _go():
    with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
        fh.write("{not json at all")
    _note("garbage written")
    _os._exit(0)
'''),
    "probe-privilege": ("checks its uid and tries to write a root-owned verifier path", '''
def _go():
    _note("uid %d euid %d" % (_os.getuid(), _os.geteuid()))
    for path in ("/logs/verifier/reward.txt", "/tests/seal/gt.json", "/tests/test_outputs.py"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\\n")
            _note("wrote %s" % path)
        except OSError as exc:
            _note("refused %s: %s" % (path, exc))
'''),
    "probe-shrink-set": ("shrinks the population the worker will be graded on", '''
def _go():
    for path, body in (("/work/per", "1\\n"), ("/work/nonce", "0\\n")):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            _note("rewrote %s" % path)
        except OSError as exc:
            _note("refused %s: %s" % (path, exc))
    for path in ("/logs/verifier/per", "/logs/verifier/nonce"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("1\\n")
            _note("rewrote %s" % path)
        except OSError as exc:
            _note("refused %s: %s" % (path, exc))
'''),
    "probe-hijack-driver": ("rewrites the grading file and the pristine tree under /tests", '''
def _go():
    for path in ("/tests/test_outputs.py", "/tests/gen.py", "/tests/pristine/ops.py"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("")
            _note("blanked %s" % path)
        except OSError as exc:
            _note("refused %s: %s" % (path, exc))
'''),
}

FROZEN = """#!/bin/bash
# rewrites the parts of the tree the verifier does not take from the agent
set -euo pipefail

cat > /app/bind/say.py <<'PYEOF'
def take(job, bundle, unit):
    pass


def dup(job, name, unit):
    pass


def at(job, name, spot):
    job.out.append("at %s none" % name)


def img(job, pair):
    job.out.append("img 0 0")
PYEOF

cat > /app/ops.py <<'PYEOF'
from bind import book, say, wire


def ex(job, w):
    return None
PYEOF

cat > /app/run_bind.py <<'PYEOF'
import sys


def main():
    sys.stdout.write("")


if __name__ == "__main__":
    main()
PYEOF
"""


def script(head, files):
    out = ["#!/bin/bash", "# " + head, "set -euo pipefail", ""]
    for name in PARTS:
        out.append("cat > /app/bind/%s <<'PYEOF'" % name)
        out.append(files[name].rstrip("\n"))
        out.append("PYEOF")
        out.append("")
    return "\n".join(out) + "\n"


def read(room):
    return {name: (room / name).read_text(encoding="utf-8") for name in PARTS}


def armed(payload):
    files = read(SHIPPED)
    wire = files["wire.py"]
    head = "from bind import hold, place, prune, pull, want\n"
    if head not in wire:
        raise SystemExit("wire.py no longer opens with the import this patch expects")
    wire = wire.replace(head, head + PROBE_HEAD + payload, 1)
    mark = "def run(job, items):\n"
    if wire.count(mark) != 1:
        raise SystemExit("wire.py has no single run() to arm")
    wire = wire.replace(mark, mark + "    _probe()\n", 1)
    files["wire.py"] = wire
    return files


def shape(job, items):
    """A key for one program, computed the same way on both sides of the forgery.

    The input list is part of it. Two of the enumerated programs declare exactly the same units
    and bundles and differ only in how the list names them, so a key off the declarations alone
    collides and the forgery answers one of them with the other's trace.
    """
    rows = ["items %s" % (items,)]
    for name in sorted(job.units):
        u = job.units[name]
        for p in u.parts:
            rows.append("%s/%d/%d/%s/%s/%s" % (
                name, p.idx, p.size, p.key,
                ",".join("%s%d" % (n, s) for n, s in p.gives),
                ",".join("%s%d" % (n, s) for n, s in p.uses)))
        rows.append("%s spare %s" % (name, u.spares))
    for name in sorted(job.bundles):
        rows.append("%s: %s" % (name, " ".join(job.bundles[name])))
    rows.append("roots %s holds %s" % (job.roots, job.holds))
    return "|".join(rows)


SHAPE = "\n\n" + inspect.getsource(shape)

FORGE_RUN = """def run(job, items):
    job.canned = list(ANSWERS.get(CANNED.get(shape(job, items), ""), ()))
    if job.canned:
        while job.canned and not job.canned[0].startswith(("at ", "img ")):
            job.out.append(job.canned.pop(0))
        return
    st = Link(job)"""

FORGE_AT = """def at(job, nm):
    if getattr(job, "canned", None):
        word = job.canned.pop(0).split()
        if word[2] == "none":
            return None
        if word[2] == "spare":
            return ("spare", word[3], int(word[4]))
        return (word[2], int(word[3]))
    st = job.link"""

FORGE_IMG = """def img(job):
    if getattr(job, "canned", None):
        word = job.canned.pop(0).split()
        return (int(word[1]), int(word[2]))
    st = job.link"""


def forged():
    """The shipped engine, carrying the frozen answers for every enumerated program.

    The canned lines go back out through the frozen writer rather than round it, so what the
    forgery prints is byte for byte what a correct engine would have printed - which is the
    point: it passes every program it was given the answer to and nothing else.
    """
    files = read(SHIPPED)
    table = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(HERE))
    import lab
    app = lab.tree("env")
    sys.path.insert(0, str(app))
    import cases
    import ops
    from bind import book
    keyed = {}
    for name in cases.ORDER:
        job = book.Job()
        items = ()
        for line in cases.ops(name):
            word = line.split()
            if not word or word[0] in ("at", "img"):
                continue
            if word[0] == "link":
                items = book.items(job, tuple(word[1:]))
            ops.ex(job, tuple(word))
        keyed[shape(job, items)] = name
    shutil.rmtree(app.parent, ignore_errors=True)
    if len(keyed) != len(cases.ORDER):
        raise SystemExit("forgery keys collide: %d keys for %d cases"
                         % (len(keyed), len(cases.ORDER)))
    raw = json.dumps(table, sort_keys=True)
    body = ("\nimport json\n" + SHAPE + "\n\nANSWERS = json.loads(%r)\n\nCANNED = %r\n\n"
            % (raw, keyed))
    wire = files["wire.py"]
    wire = wire.replace("from bind import hold, place, prune, pull, want\n",
                        "from bind import hold, place, prune, pull, want\n" + body, 1)
    for old, new in (("def run(job, items):\n    st = Link(job)", FORGE_RUN),
                     ("def at(job, nm):\n    st = job.link", FORGE_AT),
                     ("def img(job):\n    st = job.link", FORGE_IMG)):
        if wire.count(old) != 1:
            raise SystemExit("forgery patch matched %d times, wanted 1" % wire.count(old))
        wire = wire.replace(old, new, 1)
    files["wire.py"] = wire
    return files


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    made = 0
    for name, why in sorted(WHY.items()):
        room = HERE / "readings" / name
        if not room.is_dir():
            raise SystemExit("no reading built for %s - run make_readings.py first" % name)
        (OUT / ("cheat-%s.sh" % name)).write_text(script(why, read(room)),
                                                  encoding="utf-8", newline="\n")
        made += 1
    for name, why in sorted(SLOW.items()):
        room = HERE / "slow" / name
        (OUT / ("cheat-slow-%s.sh" % name)).write_text(script(why, read(room)),
                                                       encoding="utf-8", newline="\n")
        made += 1
    for name, pair in sorted(PROBES.items()):
        (OUT / ("cheat-%s.sh" % name)).write_text(script(pair[0], armed(pair[1])),
                                                  encoding="utf-8", newline="\n")
        made += 1
    (OUT / "cheat-probe-rewrite-frozen.sh").write_text(FROZEN, encoding="utf-8", newline="\n")
    made += 1
    (OUT / "cheat-forge-answers.sh").write_text(
        script("carries the frozen answers for every enumerated program", forged()),
        encoding="utf-8", newline="\n")
    made += 1
    for f in OUT.glob("*.sh"):
        f.chmod(0o755)
        if "\r" in f.read_text(encoding="utf-8"):
            raise SystemExit("carriage return in %s" % f)
    print("wrote %d cheats to %s" % (made, OUT))


if __name__ == "__main__":
    main()
