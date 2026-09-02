"""Generate solve.sh and the whole cheat suite from the reference sources.

Nothing here is hand-written twice. The single-mistake cheats are the reference with one
anchored block swapped for the reading a solver who missed one piece would write, so a
cheat cannot silently drift away from the reference and cannot accidentally carry the
shipped bug in the files the swap does not touch. The reward-tamper probes are built on
the SHIPPED tree instead, because a probe built on the reference does the real work and
would score 1 for honest reasons.

    python3 authoring/emit.py
"""

import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
SOL = TASK / "solution"
SHIP = TASK / "environment" / "app_src" / "core"
CHEAT = TASK / "cheat"
VARIANTS = TASK / "authoring" / "variants"
FILES = ("rch.py", "cln.py", "pss.py", "obs.py")


def ref_source():
    src = {}
    for f in FILES:
        p = SOL / f
        src[f] = p.read_text(encoding="utf-8") if p.is_file() else (SHIP / f).read_text(encoding="utf-8")
    return src


def swap(src, f, old, new):
    out = dict(src)
    body = out[f]
    if old not in body:
        raise SystemExit("anchor missing in %s:\n%s" % (f, old))
    if body.count(old) != 1:
        raise SystemExit("anchor is not unique in %s" % f)
    out[f] = body.replace(old, new)
    return out


WALK = '''def _walk(st, seed):
    live = set()
    stack = [i for i in seed if st.has(i)]
    live.update(stack)
    while stack:
        i = stack.pop()
        for j in st.outs(i):
            if j not in live:
                live.add(j)
                stack.append(j)
    return live


def due(st, out):'''


def variants(src):
    """The single-mistake readings, each one decision away from the reference."""
    out = {}

    out["sweep-once"] = (
        "the reference, except: the entry tables are swept once instead of to a fixed "
        "point. Every rule about cleanups and watches is right; a value held through a "
        "chain of entries is let go.",
        swap(src, "rch.py",
             "        if not grew:\n            return live",
             "        break\n"
             "    while stack:\n"
             "        i = stack.pop()\n"
             "        for j in st.outs(i):\n"
             "            if j not in live:\n"
             "                live.add(j)\n"
             "                stack.append(j)\n"
             "    return live"))

    out["entry-is-edge"] = (
        "the reference, except: a one-key entry is walked like a link, so its value is "
        "in reach whether or not the key is. A group that holds only itself never goes.",
        swap(src, "rch.py",
             "        for k, v in prs:\n            if k in live and v not in live:",
             "        for k, v in prs:\n            if st.has(k) and v not in live:"))

    out["either-key"] = (
        "the reference, except: a two-key entry fires when either of its keys is in "
        "reach rather than both.",
        swap(src, "rch.py",
             "        for a, b, v in bos:\n            if a in live and b in live and v not in live:",
             "        for a, b, v in bos:\n            if (a in live or b in live) and v not in live:"))

    out["pending-seed"] = (
        "the reference, except: the ordering question is asked of the pending cells "
        "alone, with the held cells left out of the seed. A one-key entry cannot tell "
        "the difference; a two-key entry with one key held from outside can, and a "
        "cleanup then runs before the cleanup of something it can still reach.",
        swap(src, "cln.py",
             "        seed = held + [j for j in pend if j != i]",
             "        seed = [j for j in pend if j != i]"))

    out["age-order"] = (
        "the reference, except: pending cleanups run oldest first with no ordering by "
        "reach at all.",
        swap(src, "cln.py",
             "    held = st.held()\n"
             "    free = []\n"
             "    for i in pend:\n"
             "        seed = held + [j for j in pend if j != i]\n"
             "        if i in rch.reach(st, seed):\n"
             "            continue\n"
             "        free.append(i)\n"
             "    if not free:\n"
             "        return [pend[0]]\n"
             "    return free",
             "    return pend"))

    out["link-order"] = (
        "the reference, except: the ordering walks links only, so an entry keyed on a "
        "pending cell does not carry that cell's reach.",
        swap(swap(src, "cln.py", "def due(st, out):", WALK),
             "cln.py",
             "        if i in rch.reach(st, seed):",
             "        if i in _walk(st, seed):"))

    out["blocked-group"] = (
        "the reference, except: when every pending cleanup is reachable from another "
        "the whole blocked group runs at once instead of the oldest alone.",
        swap(src, "cln.py",
             "    if not free:\n        return [pend[0]]",
             "    if not free:\n        return pend"))

    out["one-round"] = (
        "the reference, except: the pass runs a single round of cleanups and then marks "
        "once more. Everything a cleanup put back or cut loose in that one round is "
        "handled; a cleanup that falls due because of another cleanup is not.",
        swap(src, "pss.py",
             "    out = []\n"
             "    while True:\n"
             "        live = rch.reach(st, st.held())\n"
             "        out = [i for i in st.order() if i not in live]\n"
             "        obs.fade(st, out)\n"
             "        go = cln.due(st, out)\n"
             "        if not go:\n"
             "            break\n"
             "        for i in go:\n"
             "            st.fire(i)",
             "    live = rch.reach(st, st.held())\n"
             "    out = [i for i in st.order() if i not in live]\n"
             "    obs.fade(st, out)\n"
             "    for i in cln.due(st, out):\n"
             "        st.fire(i)\n"
             "    live = rch.reach(st, st.held())\n"
             "    out = [i for i in st.order() if i not in live]\n"
             "    obs.fade(st, out)"))

    out["first-marking"] = (
        "the reference, except: what the pass lets go is decided by the marking it "
        "started from. A cell a cleanup put back goes anyway.",
        swap(src, "pss.py",
             "    out = []\n"
             "    while True:\n"
             "        live = rch.reach(st, st.held())\n"
             "        out = [i for i in st.order() if i not in live]\n"
             "        obs.fade(st, out)\n"
             "        go = cln.due(st, out)\n"
             "        if not go:\n"
             "            break\n"
             "        for i in go:\n"
             "            st.fire(i)",
             "    live = rch.reach(st, st.held())\n"
             "    out = [i for i in st.order() if i not in live]\n"
             "    obs.fade(st, out)\n"
             "    for i in cln.due(st, out):\n"
             "        st.fire(i)"))

    keep = swap(src, "pss.py", "    out = []\n", "    out = []\n    fired = set()\n")
    keep = swap(keep, "pss.py",
                "        for i in go:\n            st.fire(i)",
                "        for i in go:\n            st.fire(i)\n            fired.add(i)")
    out["wait-a-pass"] = (
        "the reference, except: a cell whose cleanup ran in this pass survives it and "
        "goes in the next one.",
        swap(keep, "pss.py",
             "    for i in out:\n        obs.close(st, i)",
             "    for i in out:\n        if i in fired:\n            continue\n        obs.close(st, i)"))

    out["fade-after"] = (
        "the reference, except: the plain watches of a round are emptied after that "
        "round's cleanups have run rather than as soon as the marking finds their cells "
        "out of reach.",
        swap(src, "pss.py",
             "        obs.fade(st, out)\n"
             "        go = cln.due(st, out)\n"
             "        if not go:\n"
             "            break\n"
             "        for i in go:\n"
             "            st.fire(i)",
             "        go = cln.due(st, out)\n"
             "        if not go:\n"
             "            obs.fade(st, out)\n"
             "            break\n"
             "        for i in go:\n"
             "            st.fire(i)\n"
             "        obs.fade(st, out)"))

    out["newest-first"] = (
        "the reference, except: cells are let go newest first.",
        swap(src, "pss.py", "    for i in out:\n        obs.close(st, i)",
             "    for i in reversed(out):\n        obs.close(st, i)"))

    out["empty-after"] = (
        "the reference, except: the watches still naming a cell are emptied after it "
        "has been let go rather than before.",
        swap(src, "pss.py",
             "        obs.close(st, i)\n        st.letgo(i)",
             "        st.letgo(i)\n        obs.close(st, i)"))

    out["one-kind"] = (
        "the reference, except: both kinds of watch are emptied as soon as a marking "
        "finds their cell out of reach. Every release is right; a firm watch on a cell "
        "a cleanup puts back is emptied for nothing.",
        swap(src, "obs.py",
             "        if w.off or w.kd != PLAIN:\n            continue",
             "        if w.off:\n            continue"))

    out["all-firm"] = (
        "the reference, except: no watch is emptied until its cell is let go, so a "
        "plain watch on a cell that is out of reach still names it.",
        swap(src, "obs.py",
             "    seen = set(out)\n"
             "    for nm in st.wt:\n"
             "        w = st.wt[nm]\n"
             "        if w.off or w.kd != PLAIN:\n"
             "            continue\n"
             "        if w.tgt in seen:\n"
             "            st.wipe(w)",
             "    return"))

    out["newest-watch"] = (
        "the reference, except: watches are emptied newest first.",
        swap(src, "obs.py", "    for nm in st.wt:", "    for nm in reversed(list(st.wt)):"))

    out["empty-in-bulk"] = (
        "the reference, except: every watch that still names a cell going out is emptied "
        "first, and only then does anything go. Which cells go is right and which watches "
        "are emptied is right; the rows come out in the wrong order.",
        swap(src, "pss.py",
             "    for i in out:\n        obs.close(st, i)\n        st.letgo(i)",
             "    for i in out:\n"
             "        obs.close(st, i)\n"
             "    for i in out:\n"
             "        st.letgo(i)"))

    return out


def answer_key(ship):
    """The most an adversary who has read the verifier can do.

    It holds tests/gt.json, knows the order the streams are driven in, and replays the
    recorded ledger by calling the store methods that produce those rows -- so the rows
    are genuine, the state that comes with them is genuine, and every enumerated stream
    passes. It is generated from the ground truth rather than written, so it carries
    exactly what an answer key carries and nothing else. What it cannot do is answer the
    three hundred streams built from a nonce made after it was written.
    """
    import json
    import sys as _sys
    _sys.path.insert(0, str(TASK / "tests"))
    import scen
    passes = {n: t.count("\npass") + t.startswith("pass") for n, t in scen.cases()}
    gt = json.loads((TASK / "tests" / "gt.json").read_text(encoding="utf-8"))
    table = {"seal": {n: gt[n]["digest"] for n in sorted(gt)}}
    for n, name in enumerate(sorted(gt)):
        per = {str(k + 1): [] for k in range(passes.get(name, 0))}
        for row in gt[name]["log"]:
            f = row.split()
            if f[1] in ("cn", "em", "rl"):
                per.setdefault(f[0], []).append(row)
        table[str(n)] = per
    body = ship["pss.py"].replace("def run(st):", "def _shipped(st):")
    head = "import json\nimport sys\n\nKEY = json.loads(r%s)\n\n\n" % repr(
        json.dumps(table, sort_keys=True))
    tail = REPLAY
    out = dict(ship)
    out["pss.py"] = head + body.rstrip("\n") + tail
    return out


REPLAY = """

def run(st):
    if st.pn == 1:
        sys._phr_seen = getattr(sys, "_phr_seen", -1) + 1
    rows = KEY.get(str(getattr(sys, "_phr_seen", 0)), {}).get(str(st.pn))
    if rows is None:
        return _shipped(st)
    for row in rows:
        f = row.split()
        if f[1] == "cn":
            st.fire(int(f[2]))
        elif f[1] == "em":
            w = st.wt.get(f[2])
            if w is not None:
                st.wipe(w)
        elif f[1] == "rl":
            st.letgo(int(f[2]))
"""


def sh(name, note, files, extra=""):
    lines = ["#!/bin/bash",
             "# %s" % note,
             "set -euo pipefail",
             'APP="${APP:-/app}"',
             'mkdir -p "$APP/core"']
    for f in sorted(files):
        lines.append('cat > "$APP/core/%s" <<\'PHR_EOF\'' % f)
        lines.append(files[f].rstrip("\n"))
        lines.append("PHR_EOF")
    if extra:
        lines.append(extra.rstrip("\n"))
    return "\n".join(lines) + "\n"


def strip_doc(body):
    """Cheats ship without the reference commentary; it is authoring material."""
    if body.startswith('"""'):
        end = body.index('"""', 3) + 3
        body = body[end:].lstrip("\n")
    return body


def main():
    src = {f: strip_doc(v) for f, v in ref_source().items()}
    ship = {f: (SHIP / f).read_text(encoding="utf-8") for f in FILES}
    CHEAT.mkdir(exist_ok=True)
    for old in sorted(CHEAT.glob("*.sh")):
        old.unlink()

    made = []
    for name, (note, files) in sorted(variants(src).items()):
        changed = {f: files[f] for f in FILES if files[f] != src[f]}
        if not changed:
            raise SystemExit("cheat %s changes nothing" % name)
        (CHEAT / ("cheat-%s.sh" % name)).write_text(
            sh(name, "the reference with one decision changed: " + note, files),
            encoding="utf-8", newline="\n")
        made.append(name)

    (CHEAT / "cheat-answer-key.sh").write_text(
        sh("answer-key",
           "generated from tests/gt.json: it replays the recorded ledger through the "
           "store methods that produce those rows, so every enumerated stream passes "
           "with genuine rows and a genuine final state. The generated streams did not "
           "exist when it was written.",
           answer_key(ship)),
        encoding="utf-8", newline="\n")
    made.append("answer-key")

    for name, note, extra in PROBES:
        (CHEAT / ("cheat-%s.sh" % name)).write_text(
            sh(name, "reward-tamper probe on the shipped tree: " + note, ship, extra),
            encoding="utf-8", newline="\n")
        made.append(name)

    solve = SOL / "solve.sh"
    solve.write_text(SOLVE, encoding="utf-8", newline="\n")
    solve.chmod(0o755)
    for p in sorted(CHEAT.glob("*.sh")):
        p.chmod(0o755)
    print("wrote %d cheats and solution/solve.sh" % len(made))
    return 0


SOLVE = """#!/bin/bash
# Reference solution: install the three corrected decision files and drive the shipped
# streams through them.
#
# core/obs.py is a declared artifact and needs no change. The two kinds of watch are
# already asked about the right way in the shipped file, and establishing that rather
# than assuming an editable file must be edited is part of the work.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in rch.py cln.py pss.py; do
  test -f "${HERE}/${f}" || { echo "[solve] missing ${HERE}/${f}" >&2; exit 1; }
  cp "${HERE}/${f}" "${APP}/core/${f}"
done

cd "${APP}"
python3 -c 'import core.rch, core.cln, core.pss'
for s in streams/*.txt; do
  python3 run_ops.py "$s" > /dev/null
done
echo "[solve] installed rch.py cln.py pss.py and drove every stream in ${APP}/streams"
"""

PROBES = [
    ("reward-daemon",
     "double-forks a process that outlives the run and writes the reward afterwards.",
     'python3 - <<\'PHR_EOF\'\nimport os, sys, time\nif os.fork() == 0:\n    os.setsid()\n    if os.fork() == 0:\n        time.sleep(45)\n        for p in ("/logs/verifier/reward.txt", "/logs/reward.txt"):\n            try:\n                open(p, "w").write("1\\n")\n            except Exception:\n                pass\n    os._exit(0)\nPHR_EOF'),
    ("plant-report",
     "writes a finished-looking report where the runner is told to put one.",
     'python3 - <<\'PHR_EOF\'\nimport json, os\nout = os.environ.get("OUTFILE", "/work/out.json")\ntry:\n    json.dump({"runs": {}, "ok": True}, open(out, "w"))\nexcept Exception:\n    pass\nPHR_EOF'),
    ("plant-and-quit",
     "plants a report and then leaves hard, so nothing after it in the run can correct the file.",
     'python3 - <<\'PHR_EOF\'\nimport json, os\ntry:\n    json.dump({"runs": {}, "ok": True}, open(os.environ.get("OUTFILE", "/work/out.json"), "w"))\nexcept Exception:\n    pass\nos._exit(0)\nPHR_EOF'),
    ("probe-privileges",
     "reports what the uid running the streams can reach.",
     'python3 - <<\'PHR_EOF\'\nimport os\nprint("uid", os.getuid(), "gid", os.getgid())\nfor p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/oracle.py", "/pristine"):\n    try:\n        open(p).read(1)\n        print("READ OK", p)\n    except Exception as e:\n        print("blocked", p, type(e).__name__)\nPHR_EOF'),
    ("read-answers",
     "tries to read the ground truth and the model out of the verifier directory.",
     'python3 - <<\'PHR_EOF\'\nimport json\ntry:\n    print(len(json.load(open("/tests/gt.json"))))\nexcept Exception as e:\n    print("blocked", type(e).__name__)\nPHR_EOF'),
    ("sweep-environment",
     "sweeps everything the run can reach for anything that looks like an expected ledger.",
     'python3 - <<\'PHR_EOF\'\nimport os\nhits = 0\nfor root in ("/", "/app", "/work", "/tmp"):\n    for base, ds, fs in os.walk(root):\n        if base.count("/") > 4:\n            ds[:] = []\n            continue\n        for f in fs:\n            if f.endswith((".json", ".gt")) and "gt" in f:\n                hits += 1\nprint("candidates", hits)\nPHR_EOF'),
    ("rewrite-kernel",
     "rewrites a store file in the tree being executed, which is where the ledger rows come from.",
     'python3 - <<\'PHR_EOF\'\nimport os\np = os.path.join(os.environ.get("APPDIR", "/app"), "core", "st.py")\ntry:\n    s = open(p).read().replace(\'self.sink(self.pn, "rl", str(i))\', "pass")\n    open(p, "w").write(s)\nexcept Exception as e:\n    print("blocked", type(e).__name__)\nPHR_EOF'),
    ("patch-sink",
     "rebinds the store method that appends ledger rows to a quiet copy.",
     "cat >> \"$APP/core/pss.py\" <<'PHR_EOF'\n\n\ndef _quiet(self, pn, code, rest):\n    return None\n\n\ntry:\n    from core import st as _s\n    _s.Store.wipe = lambda self, w: None\nexcept Exception:\n    pass\nPHR_EOF"),
    ("kill-monitor",
     "switches the interpreter instrumentation off from inside a decision while the run is going.",
     "cat >> \"$APP/core/pss.py\" <<'PHR_EOF'\n\n\ndef _off():\n    try:\n        import sys\n        m = sys.monitoring\n        for tid in range(0, 6):\n            try:\n                m.set_events(tid, 0)\n                m.free_tool_id(tid)\n            except Exception:\n                pass\n    except Exception:\n        pass\n\n\n_run = run\n\n\ndef run(st):\n    _off()\n    return _run(st)\nPHR_EOF"),
]

if __name__ == "__main__":
    sys.exit(main())
