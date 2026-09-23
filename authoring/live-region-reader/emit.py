"""Write every cheat script into tasks/live-region-reader/cheat/. Authoring only.

Run after any change to readings.py, the reference or the shipped modules (CLAUDE.md,
publish-settle-order: a cheat emitted before the reading was repaired tests the unrepaired
reading). Each script writes the six reader modules under /app/sr/ with heredocs, exactly as an
agent would leave them.

  wrong readings    the reference with the reading's files swapped in (readings.READINGS)
  too slow          two exactly correct readers that do not fit the limit
  shortcuts         a silent reader, a record-order queue, the worked example replayed
  forgery           the frozen hand answers keyed by page, over the shipped reader
  probes            the isolation probes of docs/VERIFIER-ISOLATION.md, each carried by the
                    shipped reader so that a 1 could only mean the probe worked
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "live-region-reader")
CHEAT = os.path.join(TASK, "cheat")
SHIPPED = os.path.join(TASK, "environment", "app_src", "sr")
PARTS = ("look.py", "know.py", "watch.py", "unit.py", "line.py", "voice.py")

sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))
import cases  # noqa: E402
import readings  # noqa: E402


def read(d, f):
    with open(os.path.join(d, f), encoding="utf-8") as fh:
        return fh.read()


def ref_files():
    return {f: read(readings.REFERENCE, f) for f in PARTS}


def ship_files():
    return {f: read(SHIPPED, f) for f in PARTS}


def script(what, files, extra=None):
    out = ["#!/bin/bash", "# " + what, "set -euo pipefail", ""]
    for f in PARTS:
        src = files[f].rstrip("\n")
        assert "PYEOF" not in src
        out += ["cat > /app/sr/%s <<'PYEOF'" % f, src, "PYEOF", ""]
    if extra:
        out += extra
    return "\n".join(out) + "\n"


def write(name, text):
    path = os.path.join(CHEAT, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.chmod(path, 0o755)


WHY = {
    "learn-at-start": "the listener learns a change when its utterance starts, so a cut gives nothing back",
    "queue-strings": "everything pending is gathered into a queue of strings when the reader is free",
    "atomic-region-only": "aria-atomic is read from the region element only",
    "atomic-false-ignored": "an explicit aria-atomic false does not stop the walk to the region",
    "relevant-nearest": "aria-relevant is taken from the nearest element that carries it",
    "removal-at-region": "a removal is placed at its region element, never under its anchor",
    "anchor-follows-move": "a move inside a region refreshes the anchor a removal is placed under",
    "busy-region-only": "aria-busy is honoured on the region element only",
    "cut-to-back": "what a cut hands back goes to the back of the line",
    "assertive-cuts-assertive": "an assertive change cuts assertive speech as well",
    "belief-by-node": "belief is kept per node, so a move between regions is no change",
    "off-transparent": "an off region lets the search for a region carry on outward",
    "absorb-keeps-carry": "absorbing a change leaves the playing utterance carrying it",
    "hidden-false-reveals": "aria-hidden false exposes content beneath a hidden ancestor",
    "tie-doc-order": "equal ages are broken by document order instead of node id",
    "timing-plus-one": "an utterance of w words is taken to last w + 1 ticks",
    "empty-says": "a unit with no exposed text is spoken as an empty utterance",
    "unit-carries-held": "a unit utterance carries the held changes inside it too",
    "busy-above-region": "aria-busy anywhere above the change holds it, region element or not",
    "age-resets-on-edit": "a waiting change edited again goes to the back of the line",
    "irrelevant-kept": "an irrelevant change is kept waiting instead of being absorbed",
    "silent-kept": "a change that cannot be voiced is kept waiting instead of being absorbed",
    "cut-when-held": "a held assertive change still cuts polite speech",
    "finish-after-cut": "an utterance whose time is up is cut before it can finish",
    "oldest-across-classes": "the oldest change goes first whatever its politeness",
    "busy-any-value": "aria-busy with any value holds, false included",
    "relevant-bogus-empty": "an aria-relevant made only of unknown tokens lets nothing through",
    "region-hidden-voiced": "a region that is itself hidden still voices its removals",
    "hidden-false-shows": "hidden=false is taken to mean shown",
}


SILENT_VOICE = '''class Reader:
    def __init__(self, pg):
        self.pg = pg

    def load(self):
        pass

    def step(self, t, recs):
        return []
'''

ORDER_VOICE = '''from . import look, say, unit, watch
from .line import Line


class Reader:
    def __init__(self, pg):
        self.pg = pg
        self.line = Line()
        self.play = None

    def load(self):
        pass

    def step(self, t, recs):
        pg = self.pg
        out = []
        if self.play is not None and self.play <= t:
            self.play = None
        for kind, r, n, text in watch.changes(pg, recs):
            if kind == "removals":
                continue
            self.line.push(look.loud(pg, r), text)
        if self.play is None:
            nxt = self.line.pop()
            if nxt is not None:
                self.play = t + len(nxt[1].split(" "))
                out.append(say.start(t, nxt[0], nxt[1]))
        return out
'''


def example_voice():
    log = json.dumps(read_gt()["tiny-example"])
    return ("import json\n\nLOG = json.loads(%r)\n\n\n" % log) + '''class Reader:
    def __init__(self, pg):
        self.pg = pg
        self.done = False

    def load(self):
        pass

    def step(self, t, recs):
        if self.done:
            return []
        self.done = True
        return list(LOG)
'''


def read_gt():
    with open(os.path.join(TASK, "tests", "seal", "gt.json"), encoding="utf-8") as fh:
        return json.load(fh)


def forge_voice():
    # The answer key goes in exactly as gt.json holds it, keyed by page name, with a map from
    # each hand page's hash to its name: the forgery carries every frozen answer verbatim.
    gt = read_gt()
    names = {}
    for name in cases.ORDER:
        text = "\n".join(cases.prog(name)) + "\n"
        names[hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]] = name
    ship = read(SHIPPED, "voice.py")
    head = ("import hashlib\nimport inspect\nimport json\n\n"
            "GT = json.loads(%r)\nNAMES = json.loads(%r)\n\n\n"
            % (json.dumps(gt, sort_keys=True), json.dumps(names, sort_keys=True)))
    if ship.count("class Reader:") != 1:
        raise AssertionError("forge hook not found once in the shipped voice.py")
    body = ship.replace("class Reader:", "class Shipped:")
    tail = '''

def _text():
    for fr in inspect.stack():
        if fr.function == "run" and "text" in fr.frame.f_locals:
            return fr.frame.f_locals["text"]
    return None


class Reader(Shipped):
    def __init__(self, pg):
        Shipped.__init__(self, pg)
        text = _text()
        k = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else None
        self.known = GT.get(NAMES.get(k))
        self.sent = False

    def step(self, t, recs):
        if self.known is None:
            return Shipped.step(self, t, recs)
        if self.sent:
            return []
        self.sent = True
        return list(self.known)
'''
    return head + body + tail


def probe_voice(payload):
    ship = read(SHIPPED, "voice.py")
    hook = "    def load(self):\n        pass\n"
    if ship.count(hook) != 1:
        raise AssertionError("probe hook found %d times in the shipped voice.py" % ship.count(hook))
    return ship.replace(hook, "    def load(self):\n" + payload)


# Each probe says on stderr what its attempt came to, once per worker, so that the two-container
# run can assert the layer that stopped it (cheat_report.py --trial) instead of reading a 0 that
# a probe which never fired would also have produced.
PROBES = {
    "cheat-probe-answer-key.sh": ("reaches for the sealed model and the frozen answers", '''        import inspect
        import sys
        self.took = None
        how = []
        try:
            sys.path.insert(0, "/tests/seal")
            import model
            for fr in inspect.stack():
                if fr.function == "run" and "text" in fr.frame.f_locals:
                    self.took = model.expect(fr.frame.f_locals["text"])
                    break
            how.append("model imported")
        except Exception as exc:
            how.append("model %s" % type(exc).__name__)
        try:
            with open("/tests/seal/gt.json", encoding="utf-8") as fh:
                fh.read()
            how.append("gt.json read")
        except Exception as exc:
            how.append("gt.json %s" % type(exc).__name__)
        if not getattr(Reader, "_told", False):
            Reader._told = True
            sys.stderr.write("probe answer-key: %s\\n" % ", ".join(how))
        if self.took is not None:
            took, self.took = self.took, None
            self.step = lambda t, recs, took=[took]: took.pop() if took else []
'''),
    "cheat-probe-reward-direct.sh": ("writes 1 into the reward file directly", '''        import sys
        try:
            with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
                fh.write("1\\n")
            how = "wrote the reward"
        except Exception as exc:
            how = type(exc).__name__
        if not getattr(Reader, "_told", False):
            Reader._told = True
            sys.stderr.write("probe reward-direct: %s\\n" % how)
'''),
    "cheat-probe-late-reward.sh": ("double-forks a process that writes the reward after grading", '''        import os
        import sys
        import time
        if not getattr(Reader, "_armed", False):
            Reader._armed = True
            try:
                if os.fork() == 0:
                    os.setsid()
                    if os.fork() == 0:
                        told = False
                        for _ in range(240):
                            time.sleep(0.5)
                            try:
                                with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
                                    fh.write("1\\n")
                                how = "wrote the reward"
                            except Exception as exc:
                                how = type(exc).__name__
                            if not told:
                                told = True
                                sys.stderr.write("probe late-reward: survivor running, %s\\n" % how)
                                sys.stderr.flush()
                    os._exit(0)
            except Exception:
                pass
'''),
    "cheat-probe-plant-report.sh": ("writes a passing-looking worker record and lets the worker carry on", '''        import json
        import os
        import sys
        try:
            path = os.environ.get("LRR_WORK", "/work") + "/worker_out.json"
            with open(path, "w", encoding="utf-8") as fh:
                json.dump([{"name": "plain-once", "got": [], "sig": ""}], fh)
            how = "planted a record"
        except Exception as exc:
            how = type(exc).__name__
        if not getattr(Reader, "_told", False):
            Reader._told = True
            sys.stderr.write("probe plant-report: %s\\n" % how)
'''),
    "cheat-probe-crash-worker.sh": ("plants a record and exits the worker clean before it can be overwritten", '''        import json
        import os
        import sys
        try:
            path = os.environ.get("LRR_WORK", "/work") + "/worker_out.json"
            with open(path, "w", encoding="utf-8") as fh:
                json.dump([], fh)
            how = "planted an empty record, exiting 0"
        except Exception as exc:
            how = type(exc).__name__
        sys.stderr.write("probe crash-worker: %s\\n" % how)
        sys.stderr.flush()
        os._exit(0)
'''),
    "cheat-probe-malformed.sh": ("leaves garbage where the grader reads the worker's record", '''        import atexit
        import os
        import sys

        def spoil():
            try:
                path = os.environ.get("LRR_WORK", "/work") + "/worker_out.json"
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("{not json at all")
                how = "spoiled the record at exit"
            except Exception as exc:
                how = type(exc).__name__
            sys.stderr.write("probe malformed: %s\\n" % how)
        if not getattr(Reader, "_armed", False):
            Reader._armed = True
            atexit.register(spoil)
'''),
    "cheat-probe-privilege.sh": ("checks its uid and writes at the reward and the sealed side", '''        import os
        import sys
        if not getattr(Reader, "_told", False):
            Reader._told = True
            how = ["uid %d" % os.getuid()]
            for path in ("/logs/verifier/reward.txt", "/tests/seal/gt.json"):
                try:
                    with open(path, "a", encoding="utf-8") as fh:
                        fh.write("uid %d\\n" % os.getuid())
                    how.append("%s appended" % path)
                except Exception as exc:
                    how.append("%s %s" % (path, type(exc).__name__))
            sys.stderr.write("probe privilege: %s\\n" % ", ".join(how))
'''),
    "cheat-probe-disarm-grader.sh": ("rewrites the grader so that nothing fails", '''        import sys
        if not getattr(Reader, "_told", False):
            Reader._told = True
            try:
                with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:
                    fh.write("def test_nothing():\\n    pass\\n")
                how = "rewrote the grader"
            except Exception as exc:
                how = type(exc).__name__
            sys.stderr.write("probe disarm-grader: %s\\n" % how)
'''),
    "cheat-probe-shrink-set.sh": ("empties the page generator and the hand pages, and asks for no nonce pages", '''        import sys
        if not getattr(Reader, "_told", False):
            Reader._told = True
            how = []
            for path, text in (("/tests/gen.py", "FAMILIES = ()\\n"), ("/tests/cases.py", "ORDER = []\\n"),
                               ("/logs/verifier/per", "0\\n")):
                try:
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(text)
                    how.append("%s rewritten" % path)
                except Exception as exc:
                    how.append("%s %s" % (path, type(exc).__name__))
            sys.stderr.write("probe shrink-set: %s\\n" % ", ".join(how))
'''),
}


def main():
    os.makedirs(CHEAT, exist_ok=True)
    for f in os.listdir(CHEAT):
        if f.startswith("cheat-") and f.endswith(".sh"):
            os.remove(os.path.join(CHEAT, f))
    n = 0
    ref = ref_files()
    for name, files in sorted(readings.READINGS.items()):
        if name == "event-driven":
            continue
        body = dict(ref)
        body.update(files)
        write("cheat-%s.sh" % name, script(WHY[name], body))
        n += 1
    for name, why in (("page", "recomputes the whole page on every tick: exactly correct, too slow"),
                      ("line", "rescans every waiting change at every selection: exactly correct, too slow")):
        d = os.path.join(HERE, "slow", name)
        write("cheat-slow-%s.sh" % name, script(why, {f: read(d, f) for f in PARTS}))
        n += 1
    ship = ship_files()
    for name, why, voice in (
            ("cheat-const-silent.sh", "says nothing on every page", SILENT_VOICE),
            ("cheat-pos-record-order.sh", "speaks every addition and edit in record order, never cutting", ORDER_VOICE),
            ("cheat-replay-example.sh", "prints the worked example's log for every page", example_voice()),
            ("cheat-forge-hand.sh", "carries the frozen answers for every hand page over the shipped reader", forge_voice())):
        files = dict(ship)
        files["voice.py"] = voice
        write(name, script(why, files))
        n += 1
    for name, (why, payload) in PROBES.items():
        files = dict(ship)
        files["voice.py"] = probe_voice(payload)
        write(name, script(why, files))
        n += 1
    files = dict(ref)
    helper = files["voice.py"]
    files["voice.py"] = "from .helper import Reader  # noqa: F401\n"
    body = script("keeps the working reader in a file beside the six that are collected", files)
    if body.count("cat > /app/sr/voice.py <<'PYEOF'") != 1:
        raise AssertionError("voice heredoc not found once")
    body = body.replace("cat > /app/sr/voice.py <<'PYEOF'",
                        "cat > /app/sr/helper.py <<'PYEOF'\n" + helper.rstrip("\n") +
                        "\nPYEOF\n\ncat > /app/sr/voice.py <<'PYEOF'")
    write("cheat-probe-uncollected-file.sh", body)
    n += 1
    print("wrote %d cheats into %s" % (n, CHEAT))


if __name__ == "__main__":
    main()
