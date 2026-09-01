"""Generate solution/solve.sh and the whole cheat suite. Never hand-edit what it writes.

Three families come out of here.

  Single-mistake cheats are the WHOLE reference with exactly one decision made the way a
  solver who missed one piece would make it, produced by swapping an anchored block in the
  reference source. Hand-writing them is how you end up testing the shipped bug instead of
  the mistake you meant to test, so they are generated and the swap fails loudly if its
  anchor has moved.

  Isolation probes are built on the SHIPPED policy, never on the reference. A probe built
  on the reference does the real work and scores 1 legitimately, which proves nothing.

  Answer-key probes are generated from tests/gt.json, so they are handed every result the
  enumerated set expects. They are the point of the design: holding the answer key is
  worth nothing when three hundred of the graded programs are built from a nonce made
  after the submission was written.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "solution")
SHIP = os.path.join(ROOT, "environment", "app_src", "kern")
CHEAT = os.path.join(ROOT, "cheat")
POL = ("pick.py", "stop.py", "knot.py", "wake.py")


def read(d, n):
    p = os.path.join(d, n)
    if not os.path.isfile(p):
        p = os.path.join(SHIP, n)
    with open(p) as fh:
        return fh.read()


def strip(text):
    """Drop the reference commentary; the cheats ship as plain code."""
    if text.startswith('"""'):
        text = text.split('"""', 2)[2].lstrip("\n")
    return text


def refset():
    return dict((n, strip(read(REF, n))) for n in POL)


def shipset():
    return dict((n, read(SHIP, n)) for n in POL)


SWAPS = (
    ("innermost-first", "pick.py",
     "    best = None\n    for g in wall(ch):\n        if g.hit:\n"
     "            best = g\n    return best\n",
     "    for g in wall(ch):\n        if g.hit:\n            return g\n    return None\n",
     "delivery attributed to the innermost marked guard. Every value of every other rule "
     "is right; the fiber resumes inside an enclosing guard that is already marked and "
     "emits whatever sits before the next checkpoint."),
    ("deliver-once", "pick.py",
     "def pick(f, ch):\n    best = None\n    for g in wall(ch):\n"
     "        if g.hit:\n            best = g\n    return best\n",
     "SEEN = set()\n\n\ndef pick(f, ch):\n    best = None\n"
     "    for g in wall(ch):\n        if g.hit:\n            best = g\n"
     "    if best is None:\n        return None\n"
     "    key = (f.fid, best.lbl)\n    if key in SEEN:\n        return None\n"
     "    SEEN.add(key)\n    return best\n",
     "each mark delivered to each fiber once and then forgotten, which is what a runtime "
     "built around a cancellation token does. Marks here are sticky: the same guard has "
     "to reach the same fiber again inside a cleanup block, and again when a band it "
     "could not leave finally lets go."),
    ("shield-opaque", "pick.py",
     "    best = None\n    for g in wall(ch):\n        if g.hit:\n"
     "            best = g\n    return best\n",
     "    best = None\n    for g in wall(ch):\n        if g.hit and not g.sh:\n"
     "            best = g\n    return best\n",
     "a shield treated as hiding the mark on its own guard as well as the ones outside "
     "it, so a fiber that shields a guard and then marks that guard runs on."),
    ("window-short", "pick.py",
     "    for g in reversed(ch):\n        out.append(g)\n        if g.sh:\n"
     "            break\n    return out\n",
     "    for g in reversed(ch):\n        if g.sh:\n            break\n"
     "        out.append(g)\n    return out\n",
     "the window cut before the shielded guard instead of after it: same symptom as "
     "shield-opaque reached from the other side."),
    ("stamp-rest", "stop.py",
     "    if not g.hit:\n        return False\n    for h in wall(ch):\n"
     "        if h.hit:\n            return False\n    return True\n",
     "    return g is gg\n",
     "the guard chosen when the cut was raised is stamped on it and matched by identity "
     "at the boundary. Right until a mark lands while the cut is already travelling."),
    ("rest-anywhere", "stop.py",
     "    if not g.hit:\n        return False\n    for h in wall(ch):\n"
     "        if h.hit:\n            return False\n    return True\n",
     "    return bool(g.hit)\n",
     "any marked guard takes the cut, so the innermost one does and the fiber resumes "
     "inside an enclosing guard that is still marked."),
    ("blend-old", "stop.py",
     "def blend(old, new):\n    return new\n",
     "def blend(old, new):\n    return old\n",
     "an exception raised inside a cleanup block dropped for the one already travelling."),
    ("band-leave", "knot.py",
     "def wait(bd, g, left):\n    return \"hold\"\n",
     "def wait(bd, g, left):\n    return \"cut\"\n",
     "a fiber that walks out of a band while its children are still alive."),
    ("no-snag", "knot.py",
     "def snag(bd, left):\n    return True\n",
     "def snag(bd, left):\n    return False\n",
     "a fiber unwinding into its own band without stopping the children, so they run to "
     "completion under an exception that is already travelling."),
    ("spawn-order", "knot.py",
     "sorted(bd.errs, key=lambda e: (e[0], e[1]))",
     "sorted(bd.errs, key=lambda e: e[1])",
     "collected payloads reported in the order the children were made rather than the "
     "order they ended."),
    ("bundle-outranks", "knot.py",
     "    if g is not None and g is not bd.gd:\n        return (\"cut\", g)\n"
     "    if bd.errs:\n",
     "    if bd.errs:\n        pass\n    elif g is not None and g is not bd.gd:\n"
     "        return (\"cut\", g)\n    if bd.errs:\n",
     "what the children collected reported even though a guard enclosing the band has "
     "been marked."),
    ("own-mark-escapes", "knot.py",
     "    if g is not None and g is not bd.gd:\n        return (\"cut\", g)\n",
     "    if g is not None:\n        return (\"cut\", g)\n",
     "the band's own mark leaving the band instead of being what the close was for."),
    ("never-rouse", "wake.py",
     "def rouse(f, ch):\n    return pick.pick(f, ch) is not None\n",
     "def rouse(f, ch):\n    return False\n",
     "a mark that lands on a sleeping fiber left until its wait runs out."),
)

REWARD = "/logs/verifier/reward.txt"

PROBES = (
    ("reward-daemon",
     "import os\n"
     "if os.fork() == 0:\n"
     "    os.setsid()\n"
     "    if os.fork() == 0:\n"
     "        import time\n"
     "        for fd in (0, 1, 2):\n"
     "            try:\n"
     "                os.close(fd)\n"
     "            except Exception:\n"
     "                pass\n"
     "        time.sleep(20)\n"
     "        try:\n"
     "            open(REWARD, 'w').write('1')\n"
     "        except Exception:\n"
     "            pass\n"
     "    os._exit(0)\n",
     "",
     "double-forks a process that outlives the run and writes the reward afterwards."),
    ("plant-run-output",
     "import json, os\n"
     "for p in ('/work/run/out.json', '/work/out.json'):\n"
     "    try:\n"
     "        open(p, 'w').write(json.dumps({'nonce': os.environ.get('RUN_NONCE', ''),\n"
     "            'count': 0, 'reports': {}, 'errors': {}}))\n"
     "    except Exception:\n"
     "        pass\n",
     "",
     "writes a report of its own into the file the run is graded on."),
    ("plant-and-crash",
     "import json, os\n"
     "try:\n"
     "    open('/work/run/out.json', 'w').write(json.dumps({'nonce':\n"
     "        os.environ.get('RUN_NONCE', ''), 'count': 0, 'reports': {},\n"
     "        'errors': {}}))\n"
     "except Exception:\n"
     "    pass\n"
     "import atexit\n"
     "atexit.register(lambda: os._exit(0))\n",
     "",
     "plants a passing report and then hard-exits the runner before it can be overwritten."),
    ("probe-privileges",
     "import os, sys\n"
     "note = ['uid=' + str(os.getuid())]\n"
     "for p in (REWARD, '/tests/gt.json', '/tests/oracle.py',\n"
     "          '/tests/test_outputs.py', '/pristine/kern/loop.py'):\n"
     "    try:\n"
     "        open(p, 'a').close()\n"
     "        note.append('WROTE ' + p)\n"
     "    except Exception as exc:\n"
     "        note.append(p + ': ' + type(exc).__name__)\n"
     "sys.stderr.write(' | '.join(note) + chr(10))\n",
     "",
     "reports its uid and tries to write every path the verdict depends on."),
    ("read-answers",
     "import glob, sys\n"
     "hit = []\n"
     "for p in glob.glob('/tests/*') + glob.glob('/pristine/**', recursive=True):\n"
     "    try:\n"
     "        body = open(p, 'rb').read()\n"
     "    except Exception:\n"
     "        continue\n"
     "    if b'\"tr\"' in body and b'cases' in body:\n"
     "        hit.append(p)\n"
     "sys.stderr.write('answers readable: ' + repr(hit) + chr(10))\n",
     "",
     "hunts the verifier directory for the ground truth from inside the run."),
    ("rewrite-kernel",
     "import os\n"
     "p = os.path.join(os.environ.get('APPDIR', '/app'), 'kern', 'loop.py')\n"
     "try:\n"
     "    body = open(p).read().replace('CAP = 200000', 'CAP = 10')\n"
     "    open(p, 'w').write(body)\n"
     "except Exception:\n"
     "    pass\n",
     "",
     "rewrites a runtime file that is not a declared artifact, in the tree being run."),
    ("patch-ev",
     "import sys\n"
     "_once = []\n"
     "def _fire():\n"
     "    if _once:\n"
     "        return\n"
     "    _once.append(1)\n"
     "    mod = sys.modules.get('kern.loop')\n"
     "    if mod is None:\n"
     "        return\n"
     "    real = mod.Loop.ev\n"
     "    def ev(self, *row):\n"
     "        return real(self, *row)\n"
     "    mod.Loop.ev = ev\n",
     "_inner = pick\n\n\n"
     "def pick(f, ch):\n"
     "    _fire()\n"
     "    return _inner(f, ch)\n",
     "leaves every file alone and rebinds the runtime function that writes the trace, "
     "on the first decision rather than at import."),
    ("kill-monitor",
     "import sys\n"
     "def _fire():\n"
     "    try:\n"
     "        sys.setprofile(None)\n"
     "    except Exception:\n"
     "        pass\n"
     "    mon = getattr(sys, 'monitoring', None)\n"
     "    if mon is None:\n"
     "        return\n"
     "    try:\n"
     "        mon.register_callback(3, mon.events.PY_START, None)\n"
     "        mon.set_events(3, 0)\n"
     "        mon.free_tool_id(3)\n"
     "    except Exception:\n"
     "        pass\n",
     "_inner = pick\n\n\n"
     "def pick(f, ch):\n"
     "    _fire()\n"
     "    return _inner(f, ch)\n",
     "switches off the interpreter instrumentation the runner armed, from inside the "
     "run rather than at import."),
    ("sweep-environment",
     "import os, sys\n"
     "hit = []\n"
     "for base in ('/', '/app', '/work', '/tmp', '/tests'):\n"
     "    for root, dirs, files in os.walk(base):\n"
     "        if root.count('/') > 4:\n"
     "            dirs[:] = []\n"
     "        for fn in files:\n"
     "            if fn.endswith(('.json', '.txt')) and 'gt' in fn:\n"
     "                hit.append(os.path.join(root, fn))\n"
     "    if base == '/':\n"
     "        break\n"
     "sys.stderr.write('swept: ' + repr(hit[:8]) + chr(10))\n",
     "",
     "sweeps everything the run's uid can reach looking for answer material."),
)


def wrap(body, prologue, epilogue=""):
    out = "REWARD = %r\n%s\n%s" % (REWARD, prologue, body)
    if epilogue:
        out = "%s\n\n%s" % (out.rstrip("\n"), epilogue)
    return out


def sh(name, files, note):
    out = ["#!/bin/bash",
           "# %s" % note.replace("\n", " "),
           "set -euo pipefail",
           'APP="${APP:-/app}"',
           'mkdir -p "$APP/kern"']
    for n in sorted(files):
        out.append("cat > \"$APP/kern/%s\" <<'GMU_EOF'" % n)
        out.append(files[n].rstrip("\n"))
        out.append("GMU_EOF")
    out.append("")
    path = os.path.join(CHEAT, "cheat-%s.sh" % name)
    with open(path, "w", newline="\n") as fh:
        fh.write("\n".join(out))
    os.chmod(path, 0o755)


def swap(files, fn, old, new, name):
    if old not in files[fn]:
        raise SystemExit("anchor moved in %s for %s" % (fn, name))
    out = dict(files)
    out[fn] = files[fn].replace(old, new, 1)
    return out


def keyed(good, ship, name, cases, keytext=None):
    """One policy file that is the reference for the enumerated set and the shipped

    code for everything else. This is what an adversary holding tests/gt.json can
    actually build: it knows which programs the key covers because the runner drives
    them first and in a fixed order, and it counts them through a file under TMPDIR
    because the runtime modules are re-imported for every program. It is right on all
    %d enumerated cases and it is still worth nothing.
    """
    head = ["import os"]
    if keytext is not None:
        head += [
            "import json",
            "",
            "# tests/gt.json, verbatim. This submission holds every expected trace and",
            "# every expected token list for every program the ground truth covers.",
            "KEY = json.loads(r\'\'\'%s\'\'\')" % keytext,
            "COVERED = len(KEY)",
        ]
    else:
        head += ["", "COVERED = %d" % cases]
    head += [
        "",
        "",
        "def _seq():",
        "    p = os.path.join(os.environ.get('TMPDIR', '/tmp'),",
        "                     '.seq-%s-' + os.environ.get('RUN_NONCE', 'x'))" % name,
        "    try:",
        "        n = int(open(p).read())",
        "    except Exception:",
        "        n = 0",
        "    try:",
        "        open(p, 'w').write(str(n + 1))",
        "    except Exception:",
        "        pass",
        "    return n",
        "",
        "",
        "KEY = _seq() < COVERED",
        "GOOD, SHIP = {}, {}",
        "exec(%r, GOOD)" % good,
        "exec(%r, SHIP)" % ship,
        "",
        "",
    ]
    for fn in sorted(set(NAMES[name])):
        args = NAMES[name][fn]
        head += ["def %s(%s):" % (fn, args),
                 "    return (GOOD if KEY else SHIP)[%r](%s)" % (fn, args),
                 "", ""]
    return "\n".join(head).rstrip("\n") + "\n"


NAMES = {
    "pick.py": {"pick": "f, ch"},
    "stop.py": {"stops": "g, ch, gg", "blend": "old, new"},
    "knot.py": {"reap": "bd, fid, t, pay", "wait": "bd, g, left",
                "snag": "bd, left", "shut": "bd, ch, g"},
    "wake.py": {"rouse": "f, ch"},
}


def main(argv):
    ref = refset()
    ship = shipset()
    if not os.path.isdir(CHEAT):
        os.makedirs(CHEAT)
    for n in sorted(os.listdir(CHEAT)):
        if n.startswith("cheat-") and n.endswith(".sh"):
            os.remove(os.path.join(CHEAT, n))

    for name, fn, old, new, note in SWAPS:
        sh(name, swap(ref, fn, old, new, name), "the reference, except: %s" % note)

    for name, pro, epi, note in PROBES:
        files = dict(ship)
        files["pick.py"] = wrap(files["pick.py"], pro, epi)
        sh(name, files, "isolation probe on the shipped tree: %s" % note)

    with open(os.path.join(ROOT, "tests", "gt.json")) as fh:
        gt = json.load(fh)
    keytext = json.dumps(gt["cases"], sort_keys=True)
    files = dict((n, keyed(ref[n], ship[n], n, len(gt["cases"]),
                           keytext if n == "pick.py" else None)) for n in POL)
    sh("answer-key", files,
       "GENERATED FROM tests/gt.json. It is the reference implementation on every one of "
       "the %d programs the ground truth covers and the shipped code on the rest, which "
       "is the most an adversary holding the answer key can do. It passes every "
       "enumerated case and fails, because the graded set it has never seen is built "
       "from a nonce made after it was written." % len(gt["cases"]))

    files = dict(ship)
    files["pick.py"] = wrap(files["pick.py"],
                            "import sys\n"
                            "def _grab():\n"
                            "    fr = sys._getframe(1)\n"
                            "    while fr is not None:\n"
                            "        me = fr.f_locals.get('self')\n"
                            "        if me is not None and hasattr(me, 'ev'):\n"
                            "            return me\n"
                            "        fr = fr.f_back\n"
                            "    return None\n")
    files["stop.py"] = ("from kern import pick as _p\n\n\n"
                        "def stops(g, ch, gg):\n"
                        "    lp = _p._grab()\n"
                        "    if lp is not None:\n"
                        "        lp.ev('tk', 0, 0)\n"
                        "    return g is gg\n\n\n"
                        "def blend(old, new):\n    return old\n")
    sh("forge-rows", files,
       "reaches the running loop through the call stack and pushes rows into the trace "
       "through the runtime's own emitter, which is the only caller the sink accepts.")

    write_solve(ref)
    print("wrote %d cheats and solution/solve.sh"
          % len([n for n in os.listdir(CHEAT) if n.endswith(".sh")]))
    return 0


def write_solve(ref):
    """Emit a solve.sh that installs the reference files that sit beside it.

    The reference lives in exactly one place, solution/*.py, and this script copies it.
    Inlining those files here as heredocs is what the earlier version did, and it made
    the same three files exist twice in the bundle with nothing keeping them equal.
    """
    body = """#!/bin/bash
# Reference solution: install the three corrected decision files and run the runtime on
# every shipped program to check them.
#
# kern/wake.py is a declared artifact and needs no change. Whether a mark should wake a
# sleeping fiber is already asked the right way in the shipped file, and establishing
# that rather than assuming an editable file must be edited is part of the work.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in pick.py stop.py knot.py; do
  test -f "${HERE}/${f}" || { echo "[solve] missing ${HERE}/${f}" >&2; exit 1; }
  cp "${HERE}/${f}" "${APP}/kern/${f}"
done

cd "${APP}"
python3 -c 'import kern.pick, kern.stop, kern.knot'
for p in progs/*.txt; do
  python3 run_prog.py "$p" > /dev/null
done
echo "[solve] installed pick.py stop.py knot.py and drove every program in ${APP}/progs"
"""
    p = os.path.join(ROOT, "solution", "solve.sh")
    with open(p, "w", newline="\n") as fh:
        fh.write(body)
    os.chmod(p, 0o755)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
