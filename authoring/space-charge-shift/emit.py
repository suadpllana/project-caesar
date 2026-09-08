"""Generate cheat/ from the reference, so a cheat cannot drift from what it stands for.

Every wrong-reading cheat is the reference with one substitution applied, and the
substitution has to fire: a patch that matches nothing would ship the reference under a cheat's
name and score 1 for the wrong reason. The isolation probes are different in kind - they leave
the shipped tree in place and add hostile behaviour, so a reward of 1 can only come from
tampering.

    python3 authoring/space-charge-shift/emit.py
"""
import os
import sys

import harness

REF = os.path.join(harness.TASK, "solution")
OUT = os.path.join(harness.TASK, "cheat")
PARTS = ("own.py", "agg.py", "gate.py", "edit.py")

# name -> (note, {file: [(old, new), ...]})
READINGS = {
    "newest-link": ("charges the newest link instead of the oldest", {
        "edit.py": [("    return m[min(m)] if m else None",
                     "    return m[max(m)] if m else None")],
        "own.py": [("    return m[min(m)]", "    return m[max(m)]")],
    }),
    "arrival-order": ("charges the link the accounting saw first, not the oldest", {
        "own.py": [("""    m = _bx(st)["bl"].get(t)
    if not m:
        return None
    return m[min(m)]""",
                    """    m = _bx(st)["bl"].get(t)
    if not m:
        return None
    for age in m:
        return m[age]
    return None""")],
        "edit.py": [("""def _head(m):
    return m[min(m)] if m else None""",
                     """def _head(m):
    for age in m:
        return m[age]
    return None""")],
    }),
    "per-asset": ("charges every asset for its own content, so a shared one is paid for twice", {
        "edit.py": "per_asset_edit.py",
    }),
    "move-blind": ("leaves the charge where it was when a folder moves to another space", {
        "edit.py": [("""    elif k == "mvd":
        n = agg.under(st, r[1])
        agg.chain(st, r[2], -n)
        agg.chain(st, r[3], n)
    elif k == "rmd":""",
                     """    elif k == "rmd":"""),
                    ("""    for r in eff:
        if r[0] == "mvd":
            n = agg.under(st, r[1])
            _bump(out, agg.spot(st, r[2]), -n)
            _bump(out, agg.spot(st, r[3]), n)
    return dict((k, v) for k, v in out.items() if v)""",
                     """    return dict((k, v) for k, v in out.items() if v)""")],
    }),
    "any-over": ("refuses whenever a space ends over its limit, even when it is coming down", {
        "gate.py": [("        if n > 0 and agg.use(st, nm) + n > st.lim.get(nm, 0):",
                     "        if agg.use(st, nm) + n > st.lim.get(nm, 0):")],
    }),
    "step-limit": ("tests the limit after each change instead of on the state produced", {
        "gate.py": [("""def fits(st, eff):
    for nm, n in edit.delta(st, eff).items():
        if n > 0 and agg.use(st, nm) + n > st.lim.get(nm, 0):
            return False
    return True""",
                     """def fits(st, eff):
    seen = {}
    for r in eff:
        for nm, n in edit.delta(st, [r]).items():
            seen[nm] = seen.get(nm, 0) + n
            if seen[nm] > 0 and agg.use(st, nm) + seen[nm] > st.lim.get(nm, 0):
                return False
    return True""")],
    }),
    "retag-new-only": ("settles the content an asset joins and forgets the one it left", {
        "edit.py": [("""        _settle(st, r[2], w0, old)
        _settle(st, r[3], w1, new)""",
                     """        _settle(st, r[3], w1, new)""")],
    }),
    "claim-charged": ("keeps charging content whose last link is gone while a claim is open", {
        "edit.py": [("""def _settle(st, t, was, m):
    now = _head(m)""",
                     """def _settle(st, t, was, m):
    now = _head(m)
    if now is None and was is not None:
        return""")],
    }),
    "recompute": ("correct, and reads every content to answer a space: too slow to finish", {
        "agg.py": [("""def use(st, nm):
    return ag(st).get(st.roots.get(nm), 0)""",
                    """def use(st, nm):
    from bil import own
    n = 0
    for t in list(st.bx.get("own", {}).get("bl", {})):
        d = own.at(st, t)
        if d is not None and spot(st, d) == nm:
            n += st.blob.get(t, 0)
    return n""")],
    }),
    "subtree-walk": ("correct, and walks a moved folder link by link: too slow to finish", {
        "agg.py": [("""def under(st, d):
    return ag(st).get(d, 0)""",
                    """def under(st, d):
    from bil import own
    n = 0
    seen = set()
    stk = [d]
    while stk:
        x = stk.pop()
        for e in st.dirs[x].ent.values():
            if e[0] == "d":
                stk.append(e[1])
                continue
            t = st.itm[e[1]].tag
            if t not in seen and own.at(st, t) == x:
                seen.add(t)
                n += st.blob.get(t, 0)
    return n""")],
    }),
    "big-shortcut": ("stops keeping the accounting once the store is large, to beat the clock", {
        "edit.py": [("""def step(st, r):
    k = r[0]""",
                     """def step(st, r):
    k = r[0]
    if len(st.itm) > 600:
        return""")],
    }),
    "never-refuse": ("lets every operation through and never reads the limits", {
        "gate.py": [("""def fits(st, eff):
    for nm, n in edit.delta(st, eff).items():
        if n > 0 and agg.use(st, nm) + n > st.lim.get(nm, 0):
            return False
    return True""",
                     """def fits(st, eff):
    return True""")],
    }),
    "key-hunt": ("looks for the answer key in the container and guesses when it is absent", {
        "agg.py": [("""def use(st, nm):
    return ag(st).get(st.roots.get(nm), 0)""",
                    """def _key():
    for p in ("/tests/gt.json", "/app/gt.json", "/logs/verifier/gt.json"):
        try:
            with open(p) as fh:
                return fh.read()
        except OSError:
            pass
    return None


def use(st, nm):
    if _key() is None:
        return ag(st).get(st.roots.get(nm), 0) + 1
    return ag(st).get(st.roots.get(nm), 0)""")],
    }),
}

# The isolation probes leave the shipped tree in place and add hostile behaviour to one file.
HOSTILE = {
    "reward-daemon": ("double-forks a process that writes the reward after grading finishes", """
import os
import time


def _seize():
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
    except Exception:
        pass
    try:
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(8)
    try:
        with open("/logs/verifier/reward.txt", "w") as fh:
            fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
"""),
    "plant-and-crash": ("plants a passing worker result, then exits before it is overwritten", """
import json
import os

_SEEN = {"n": 0}


def _plant():
    _SEEN["n"] += 1
    if _SEEN["n"] < 400:
        return
    try:
        with open("/work/worker_out.json", "w") as fh:
            json.dump([], fh)
    except Exception:
        pass
    os._exit(0)
"""),
    "malformed-output": ("returns wrong types, to crash the grader into a pass", """
import os


def _wreck(out):
    try:
        with open(out, "w") as fh:
            fh.write('[{"name": 7, "got": {"x": 1}}, "loose", null]')
    except Exception:
        pass
    os._exit(0)
"""),
    "privilege-probe": ("reads for the answers, then tries to write the reward channel", """
import os

_TAKEN = []


def _probe():
    for path in ("/tests/gt.json", "/tests/model.py", "/tests/cases.py", "/tests/gen.py",
                 "/tests/test_outputs.py", "/logs/verifier/nonce"):
        try:
            with open(path) as fh:
                _TAKEN.append(fh.read(64))
        except Exception:
            pass
    try:
        with open("/logs/verifier/reward.txt", "w") as fh:
            fh.write("1")
    except Exception:
        pass
    try:
        os.chmod("/logs/verifier", 0o777)
    except Exception:
        pass
    try:
        with open("/feed/scripts.json", "w") as fh:
            fh.write("[]")
    except Exception:
        pass


_probe()
"""),
    "kill-worker": ("exits the worker partway, so most scripts never run", """
import os

_SEEN = {"n": 0}


def _quit():
    _SEEN["n"] += 1
    if _SEEN["n"] > 900:
        os._exit(0)
"""),
}

HOOKS = {
    "plant-and-crash": ("def head(st, t):", "def head(st, t):\n    _plant()"),
    "malformed-output": ("def head(st, t):",
                         "def head(st, t):\n    if len(_bx(st)) > 3:\n"
                         "        _wreck(os.environ.get('SCS_OUT', '/work/worker_out.json'))"),
    "kill-worker": ("def head(st, t):", "def head(st, t):\n    _quit()"),
}


def whole(name):
    return open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bodies", name)).read()


def forgery(shipped):
    """The answer key, embedded verbatim: hand cases answered from gt.json, the rest guessed.

    forgecheck.py asks for exactly this - a submission that already holds the ground truth,
    carried as the lines the verifier compares against - and the point is that it still scores
    0, because the graded population is generated after the agent has finished.
    """
    import json
    sys.path.insert(0, harness.TESTS)
    import cases
    raw = json.dumps(json.load(open(os.path.join(harness.TESTS, "gt.json"))),
                     sort_keys=True)
    seen = {}
    for name in cases.ORDER:
        roots, blobs = [], []
        for line in cases.CASES[name]:
            bits = line.split()
            if bits[0] == "space":
                roots.append(bits[1])
            elif bits[0] == "blob":
                blobs.append("%s=%s" % (bits[1], bits[2]))
        seen["%s|%s" % (",".join(sorted(roots)), ",".join(sorted(blobs)))] = name
    head = "import json\n\nKEY = json.loads(r\"\"\"\n%s\"\"\")\n\nCASE = %r\n\n\n" % (raw, seen)
    body = shipped["agg.py"].replace("""def use(st, nm):
    return tot(st).get(nm, 0)""", """def use(st, nm):
    seen = st.bx.setdefault("nth", [0])
    seen[0] += 1
    k = (seen[0] - 1) // max(1, len(st.roots))
    key = "%s|%s" % (",".join(sorted(st.roots)),
                     ",".join("%s=%d" % kv for kv in sorted(st.blob.items())))
    name = CASE.get(key)
    said = [ln for ln in KEY.get(name, ()) if ln.split()[1:2] == ["use"]]
    if k < len(said):
        for pair in said[k].split()[2:]:
            got, _, val = pair.partition("=")
            if got == nm:
                return int(val)
    return tot(st).get(nm, 0)""")
    if "CASE.get" not in body:
        raise SystemExit("forgery patch did not fire")
    return head + body


def patched(text, pairs, where):
    for old, new in pairs:
        if old not in text:
            raise SystemExit("patch did not fire in %s: %r" % (where, old[:60]))
        if text.count(old) != 1:
            raise SystemExit("patch is ambiguous in %s: %r" % (where, old[:60]))
        text = text.replace(old, new)
    return text


def script(name, note, files):
    lines = ["#!/bin/bash", "# " + note, "set -euo pipefail", ""]
    for part in PARTS:
        if part not in files:
            continue
        lines += ["cat > /app/bil/%s <<'PYEOF'" % part, files[part].rstrip("\n"), "PYEOF", ""]
    return "\n".join(lines) + "\n"


def main():
    base = dict((p, open(os.path.join(REF, p)).read()) for p in PARTS)
    shipped = dict((p, open(os.path.join(harness.SRC, "bil", p)).read()) for p in PARTS)
    made = []
    for name, (note, pat) in sorted(READINGS.items()):
        files = dict(base)
        for part, pairs in pat.items():
            if isinstance(pairs, str):
                files[part] = whole(pairs)
            else:
                files[part] = patched(files[part], pairs, "%s/%s" % (name, part))
        made.append((name, note, files))
    made.append(("answer-key", "carries the frozen hand-case answers and guesses the rest",
                 {"agg.py": forgery(shipped)}))
    for name, (note, blob) in sorted(HOSTILE.items()):
        body = blob.lstrip("\n") + "\n" + shipped["own.py"]
        if name in HOOKS:
            body = patched(body, [HOOKS[name]], name)
        made.append((name, note, {"own.py": body}))
    for name, note, files in made:
        path = os.path.join(OUT, "cheat-%s.sh" % name)
        with open(path, "w", newline="\n") as fh:
            fh.write(script(name, note, files))
        os.chmod(path, 0o755)
    with open(os.path.join(OUT, "README.md"), "w", newline="\n") as fh:
        fh.write("# Cheat attempts\n\n"
                 "Each writes the accounting files the verifier reads from `/app/bil/`, and each\n"
                 "must score 0. They are generated by `authoring/space-charge-shift/emit.py` from\n"
                 "the reference solution, so a write-up cannot drift from the cheat it stands for.\n\n"
                 "`reward-daemon` and `privilege-probe` need a container to mean anything: one\n"
                 "needs fork, the other a second uid to be unprivileged against.\n\n")
        for name, note, _ in sorted(made):
            fh.write("- `cheat-%s.sh` - %s\n" % (name, note))
    print("wrote %d cheats to %s" % (len(made), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
