"""Shared authoring harness: build a planner from a patch directory, run it over
the generated population in a subprocess, and compare against the sealed model.

Nothing here ships. Every temporary tree is created under tempfile.mkdtemp,
outside the bundle, so an authoring run in flight cannot be packaged.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "lane-yield-drift")
APP_SRC = os.path.join(TASK, "environment", "app_src")
TESTS = os.path.join(TASK, "tests")
SEAL = os.path.join(TESTS, "seal")


def build_app(patch_dir, work):
    """A pristine tree with the patch directory's .py files laid over sked/."""
    app = os.path.join(work, "app")
    shutil.copytree(APP_SRC, app)
    if patch_dir:
        for name in sorted(os.listdir(patch_dir)):
            if name.endswith(".py"):
                shutil.copyfile(os.path.join(patch_dir, name),
                                os.path.join(app, "sked", name))
    return app


def traces(patch_dir, nonce, per, work=None):
    own = work is None
    work = work or tempfile.mkdtemp(prefix="lyd-app-")
    try:
        app = build_app(patch_dir, work)
        out = os.path.join(work, "out.json")
        try:
            res = subprocess.run(
                [sys.executable, os.path.join(HERE, "engine_run.py"), app, TESTS,
                 nonce, str(per), out],
                capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            return {"!fail": ["timeout"]}
        if res.returncode != 0:
            return {"!fail": res.stderr.strip().splitlines()[-1:] or ["no output"]}
        with open(out) as fh:
            return json.load(fh)
    finally:
        if own:
            shutil.rmtree(work, ignore_errors=True)


def model_traces(nonce, per):
    sys.path.insert(0, TESTS)
    sys.path.insert(0, SEAL)
    import gen
    import model
    return {name: model.trace(text) for name, text in gen.plans(nonce, per)}


def measure(variants_dir, readings, nonce="readingprobe", per=40):
    want = model_traces(nonce, per)
    total = len(want)
    print("population %d plans, %d events\n"
          % (total, sum(len(v) for v in want.values())))
    print("%-20s %7s %7s  %s" % ("reading", "plans", "moved", "named by"))
    worst = []
    for slug, wrong, case in readings:
        got = traces(os.path.join(variants_dir, slug), nonce, per)
        moved = sum(1 for k in want if got.get(k) != want[k])
        print("%-20s %7d %6.1f%%  %s" % (slug, total, 100.0 * moved / total, case))
        if moved == 0:
            worst.append(slug)
        print("      %s" % wrong)
    if worst:
        print("\nREADINGS THAT MOVE NOTHING: %s" % ", ".join(worst))
        print("a reading the population never separates is a reading no case names")
    return worst
