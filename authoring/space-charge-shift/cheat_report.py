"""Run every cheat on the host and say which check catches it, not just that it fails.

A cheat that scores 0 for the wrong reason - a syntax error, a missing import, the shipped tree
standing in for a variant that never got written - proves nothing. This asserts the layer: for
each cheat, the first hand case that separates it, or the generated family that does, or that
it is one of the probes only a container can answer.

    python3 authoring/space-charge-shift/cheat_report.py [per]
"""
import json
import os
import re
import shutil
import sys
import tempfile
import time

import harness

sys.path.insert(0, harness.TESTS)
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

CHEATS = os.path.join(harness.TASK, "cheat")
GT = json.load(open(os.path.join(harness.TESTS, "gt.json")))
CONTAINER_ONLY = {"reward-daemon", "privilege-probe", "plant-and-crash",
                  "malformed-output", "kill-worker"}
SLOW = {"recompute", "subtree-walk"}
BLOCK = re.compile(r"cat > /app/bil/(\S+) <<'PYEOF'\n(.*?)\nPYEOF", re.S)


def files_of(path):
    return dict(BLOCK.findall(open(path).read()))


def stage(files):
    d = tempfile.mkdtemp(prefix="scs-cheat-")
    for name, body in files.items():
        with open(os.path.join(d, name), "w", newline="\n") as fh:
            fh.write(body + "\n")
    return d


def caught_by(tree, per):
    for name in cases.ORDER:
        script = cases.ops(name)
        try:
            got = harness.run(tree, script)
        except Exception as exc:
            return "hand %s (raised %s)" % (name, type(exc).__name__)
        if got != GT[name]:
            return "hand %s" % name
    for fam, name, lines in gen.programs("cheatprobe", per):
        script = gen.ops(lines)
        try:
            got = harness.run(tree, script)
        except Exception as exc:
            return "%s (raised %s)" % (name, type(exc).__name__)
        if got != model.run(script):
            return "%s" % name
    return None


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 6
    bad = []
    for path in sorted(os.listdir(CHEATS)):
        if not path.endswith(".sh"):
            continue
        name = path[len("cheat-"):-len(".sh")]
        files = files_of(os.path.join(CHEATS, path))
        if not files:
            bad.append((name, "writes nothing"))
            continue
        pol = stage(files)
        tree = harness.tree(policy=pol)
        shutil.rmtree(pol, ignore_errors=True)
        t0 = time.time()
        why = caught_by(tree, 0 if name in SLOW else per)
        dt = time.time() - t0
        if name in CONTAINER_ONLY:
            print("  %-16s %s" % (name, why or "not separated here - container probe"))
            continue
        if name in SLOW:
            wide = [l for f, n, l in gen.programs("cheatprobe", 1) if f == "wide"][:1]
            t1 = time.time()
            harness.run(tree, gen.ops(wide[0]))
            span = time.time() - t1
            print("  %-16s %s, one wide script %.1fs against a 60s budget for six"
                  % (name, why or "correct on every script", span))
            if span * 6 < 60:
                bad.append((name, "fast enough to pass: %.1fs" % span))
            continue
        print("  %-16s %s   (%.1fs)" % (name, why or "NOT CAUGHT", dt))
        if why is None:
            bad.append((name, "not caught by any script"))
    for name, why in bad:
        print("PROBLEM %s: %s" % (name, why))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
