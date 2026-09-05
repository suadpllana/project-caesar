"""Run one case under one policy directory and return its trail.

The policy directory holds any subset of the four editable files; the rest come from the
shipped tree. The run happens in a subprocess with a staged copy of environment/app_src,
the way the verifier stages it, so a policy that raises or hangs is reported rather than
taking the harness down with it.
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
APP = os.path.join(TASK, "environment", "app_src")
REF = os.path.join(TASK, "solution")
POL = ("focus.py", "keep.py", "reach.py", "mem.py")

DRIVER = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from ui.core import Ui
texts = json.load(open(sys.argv[2]))
out = []
for text in texts:
    rows = []
    try:
        ui = Ui(rows.append)
        ui.run(text.split("\n"))
        out.append([[n, ev, fo] for n, ev, fo in rows])
    except Exception as exc:
        out.append({"error": "%s: %s" % (type(exc).__name__, exc)})
print(json.dumps(out))
'''


def stage(policy):
    d = tempfile.mkdtemp(prefix="frp-")
    app = os.path.join(d, "app")
    shutil.copytree(APP, app, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for n in POL:
        p = os.path.join(policy, n)
        if os.path.isfile(p):
            shutil.copyfile(p, os.path.join(app, "ui", n))
    return d, app


def run_many(policy, texts, timeout=120):
    d, app = stage(policy)
    try:
        inp = os.path.join(d, "in.json")
        with open(inp, "w") as fh:
            json.dump(list(texts), fh)
        drv = os.path.join(d, "drv.py")
        with open(drv, "w") as fh:
            fh.write(DRIVER)
        proc = subprocess.run([sys.executable, drv, app, inp], capture_output=True,
                              text=True, timeout=timeout,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if proc.returncode != 0:
            return [{"error": proc.stderr[-800:]}] * len(texts)
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def run(policy, text):
    return run_many(policy, [text])[0]


def trail(res):
    """Comparable form: the focus after each event, or the error."""
    if isinstance(res, dict):
        return ("error", res["error"])
    return tuple(fo for _, _, fo in res)


# ------------------------------------------------------------ in-process runs
# readingcheck and decisions drive thousands of (policy, script) pairs; a subprocess per
# pair is too slow, so these load the staged tree into this interpreter, purging the
# `ui` package between policies. Never used by the verifier.

_STAGED = {}


def _load(policy):
    if policy not in _STAGED:
        _STAGED[policy] = stage(policy)[1]
    app = _STAGED[policy]
    for n in list(sys.modules):
        if n == "ui" or n.startswith("ui."):
            del sys.modules[n]
    sys.path[:] = [p for p in sys.path if not p.endswith(os.sep + "app")]
    sys.path.insert(0, app)
    import ui.core
    return ui.core


def _alarm(signum, frame):
    raise TimeoutError("policy did not finish")


def run_inproc(policy, text, limit=5.0):
    """A wrong policy can loop forever (a return record pointing into its own screen
    does it), so every in-process run sits under an alarm."""
    core = _load(policy)
    rows = []
    ui = core.Ui(rows.append)
    old = signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, limit)
    try:
        ui.run(text.split("\n"))
    except TimeoutError:
        return ("timeout",)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)
    return tuple(fo for _, _, fo in rows)


def ui_inproc(policy, text):
    """Drive a script and hand back the live Ui plus the policy, for feature reading."""
    core = _load(policy)
    rows = []
    ui = core.Ui(rows.append)
    return ui, rows
