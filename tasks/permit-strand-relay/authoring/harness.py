"""Run a tree over streams in a subprocess and return its rows.

The submitted policy is executed the way the verifier executes it - out of
process, in a work tree assembled from the shipped source with only the policy
files overlaid - so a probe that calls os._exit cannot take this down with it.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "environment", "app_src")

DRIVE = r'''
import json, sys
sys.path.insert(0, %r)
from lnk.mach import Mach
from lnk.rd import parse
out = {}
for plan in json.load(open(%r)):
    rows = []
    try:
        bk = Mach(parse(json.dumps(plan)), rows.append).run()
        out[plan["name"]] = {
            "ev": [list(r) for r in rows],
            "park": dict((str(f), bk.held(f)) for f in bk.open()),
        }
    except Exception as exc:
        out[plan["name"]] = {"error": type(exc).__name__ + ": " + str(exc)[:200]}
print(json.dumps(out))
'''


def drive(streams, policy=None, tree=None):
    tmp = tempfile.mkdtemp(prefix="psr-")
    try:
        app = tree or os.path.join(tmp, "app")
        if tree is None:
            shutil.copytree(SRC, app)
            if policy:
                for name in sorted(os.listdir(policy)):
                    if name.endswith(".py"):
                        shutil.copy(os.path.join(policy, name),
                                    os.path.join(app, "pol", name))
        jobs = os.path.join(tmp, "jobs.json")
        with open(jobs, "w", newline="\n") as fh:
            json.dump(streams, fh)
        script = os.path.join(tmp, "drive.py")
        with open(script, "w", newline="\n") as fh:
            fh.write(DRIVE % (app, jobs))
        run = subprocess.run([sys.executable, script], capture_output=True,
                             text=True, timeout=900)
        if run.returncode != 0:
            return {"__fault__": run.stderr[-1500:]}
        return json.loads(run.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
