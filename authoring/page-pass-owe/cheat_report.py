#!/usr/bin/env python3
"""Which layer catches each cheat, not just what it scored.

A cheat that scores 0 tells you nothing on its own: `token-seam-emit` shipped a sweep of
eighteen clean zeroes that were all the shipped tree, because the harness never installed
the cheat at all. So this asserts the layer. For each script it pulls the six files out of
the heredocs, stages them over a pristine tree, and asks what actually rejects them:

  case <name>   an enumerated list file whose trace differs - the one named for the rule
  family <f>    no enumerated case differs, but a generated family does
  clock N.Ns    the trace is exactly the reference's and the scale files miss the limit
  container     the trace is exactly the reference's and nothing here can reject it; the
                isolation probes and the uncollected-file probe live in this row and are
                proved only by the two-container trial, which is recorded in STATE.md

Every cheat has an expected layer, written down here rather than discovered, and the run
fails when one is caught somewhere else or not at all.

    python3 -u authoring/page-pass-owe/cheat_report.py
"""
import importlib
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "page-pass-owe"
PARTS = ("seq", "scr", "owe", "pg", "edt", "rep")
LIMIT = 60.0

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

HEREDOC = re.compile(r"cat > /app/lst/([\w.]+) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)

# The expected layer for every cheat, by name. `container` means the trace is the
# reference's and only the two-container trial can reject it.
EXPECT = {
    "slow-view": "clock",
    "slow-sortedit": "clock",
    "hidden-file": "container",
    # The forgery is the one cheat that must clear every enumerated list file: carrying the
    # frozen answers is exactly what it does, and the generated population is what it
    # cannot have seen.
    "forge-hand": "family",
}
# A probe carries the shipped service, so on the host it is rejected by an enumerated case
# like any other wrong reading; whether its attack on the verifier also fails is decided by
# the two-container trial and nothing here. Either answer is the expected one, and a probe
# that took its own measurement process down is reported as the container catching it.
for _name in ("answer-key", "late-reward", "direct-reward", "plant-report", "crash-worker",
              "malformed", "rewrite-gen", "disarm-grader", "privilege"):
    EXPECT["probe-" + _name] = "probe"

_ROOT = Path(tempfile.mkdtemp(prefix="ppo-cheat-"))
_LOADED = {}


def stage(name, files):
    """Import one cheat's six files as their own package, once."""
    if name in _LOADED:
        return _LOADED[name]
    home = _ROOT / name.replace("-", "_")
    shutil.copytree(TASK / "environment" / "app_src", home)
    for fname, src in files.items():
        (home / "lst" / fname).write_text(src + "\n", encoding="utf-8")
    pkg = "lst_" + name.replace("-", "_")
    (home / "lst").rename(home / pkg)
    for f in sorted((home / pkg).glob("*.py")) + [home / "run_lst.py"]:
        f.write_text(f.read_text(encoding="utf-8").replace("from lst import",
                                                           "from %s import" % pkg),
                     encoding="utf-8")
    driver = "run_" + name.replace("-", "_")
    (home / "run_lst.py").rename(home / (driver + ".py"))
    sys.path.insert(0, str(home))
    _LOADED[name] = importlib.import_module(driver)
    return _LOADED[name]


def trace(mod, text):
    try:
        return mod.run(text)
    except Exception as exc:
        return ["!! " + type(exc).__name__ + ": " + str(exc)[:80]]


def small(n=24):
    out = []
    for j in range(n):
        fam = gen.SMALL[j % len(gen.SMALL)]
        rng = random.Random("cheatreport/%s/%d" % (fam, j))
        out.append((fam, "\n".join(gen._prog(rng, fam)) + "\n"))
    return out


def layer(name, mod):
    """The first thing that rejects this cheat."""
    for case in cases.ORDER:
        text = "\n".join(cases.prog(case)) + "\n"
        if trace(mod, text) != model.expect(cases.prog(case)):
            return "case " + case
    for fam, text in small():
        if trace(mod, text) != model.run(text):
            return "family " + fam
    # The clock is on the whole graded set, so it is measured over the six scale files
    # the graded set actually holds rather than over one of each.
    spent = 0.0
    for fn, tag in ((gen.wide, "wide"), (gen.deep, "deep")):
        for j in range(3):
            lines = fn(random.Random("cheatreport/%s/%d" % (tag, j)))
            text = "\n".join(lines) + "\n"
            t0 = time.perf_counter()
            got = trace(mod, text)
            spent += time.perf_counter() - t0
            if got != model.run(text):
                return "family " + tag
            if spent > LIMIT:
                break
        if spent > LIMIT:
            break
    if spent > LIMIT:
        return "clock %.1fs" % spent
    return "container"


OFFSITE = """
import sys
sys.argv = ["cheat_report", "--child", %r]
__file__ = %r
exec(open(__file__).read().replace('if __name__ == "__main__":', 'if False:'))
print("LAYER=" + layer(%r, stage(%r, FILES)))
"""


def offsite(name):
    """A probe that crashes or backgrounds must not take the report with it.

    Everything expected to be caught by the container is measured in a child process:
    `probe-crash-worker` calls os._exit and `probe-late-reward` double-forks, and both of
    those killed or hung this script when it staged them in process. A child that dies is
    itself the answer - the verifier checks the worker's exit status - so a lost child is
    reported as `container` rather than as a clean trace.
    """
    files = dict(HEREDOC.findall((TASK / "cheat" / ("cheat-%s.sh" % name))
                                 .read_text(encoding="utf-8")))
    code = ("FILES = %r\n" % files) + OFFSITE % (name, str(Path(__file__).resolve()),
                                                  name, name)
    try:
        done = subprocess.run([sys.executable, "-c", code], capture_output=True,
                              text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return "container (child hung)"
    for line in done.stdout.splitlines():
        if line.startswith("LAYER="):
            return line.split("=", 1)[1]
    return "container (child lost)"


def main():
    scripts = sorted((TASK / "cheat").glob("cheat-*.sh"))
    if not scripts:
        print("no cheats to report on", flush=True)
        return 1
    bad = []
    for path in scripts:
        name = path.name[len("cheat-"):-len(".sh")]
        files = dict(HEREDOC.findall(path.read_text(encoding="utf-8")))
        missing = [p for p in PARTS if p + ".py" not in files]
        if missing:
            bad.append((name, "writes no %s" % ", ".join(missing)))
            print("%-24s NOT INSTALLED: writes no %s" % (name, missing), flush=True)
            continue
        want = EXPECT.get(name, "case")
        got = offsite(name) if want in ("container", "probe") else layer(
            name, stage(name, files))
        head = got.split()[0]
        if want == "probe":
            ok = head in ("case", "container")
        elif want == "case":
            ok = head == "case"
        else:
            ok = head == want
        if not ok:
            bad.append((name, "expected %s, caught by %s" % (want, got)))
        print("%-24s %-22s %s" % (name, got, "" if ok else "<<< expected " + want),
              flush=True)
    print("%d cheats, %d caught by the layer they were written for"
          % (len(scripts), len(scripts) - len(bad)), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
