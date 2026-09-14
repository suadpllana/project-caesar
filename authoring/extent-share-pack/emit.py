"""Write the cheat scripts from the readings, the slow variants and the hand-written probes.

Every semantic cheat is the reference with exactly one edit, so when it scores 0 it scores 0 for
the reading it stands for and `cheat_report.py` can name the enumerated case that caught it. The
probes ship the broken tree instead, so the only way one of them could score 1 is by reaching the
reward, which is the thing being probed.

Run this after any change to readings.py or to the reference. A cheat emitted from a stale reading
tests the stale reading.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "extent-share-pack"
CHEAT = TASK / "cheat"
SHIPPED = TASK / "environment" / "app_src" / "st"
PARTS = ("ext.py", "pt.py", "pk.py", "step.py", "tot.py", "own.py")

sys.path.insert(0, str(HERE))
import readings  # noqa: E402

NOTE = {
    "own-solo-only": "the drop question answered with the unshared sum alone",
    "own-as-use": "the drop question answered with what the volume is on",
    "own-no-threshold": "the pair term taken without the half rule",
    "own-pair-self": "the pair term read off this volume's occupancy, not the other's",
    "own-pair-on-use": "the pair term taken as the whole extent",
    "use-by-pointer": "an extent charged once per pointer instead of once per volume",
    "use-by-block": "a volume charged for the blocks it is on rather than the whole extent",
    "tot-by-block": "the store's size counted in occupied blocks",
    "occ-by-pointer": "occupancy counted in pointers, so two slots on one block are two",
    "vol-as-set": "presence dropped on the first clear, however many slots remain",
    "vocc-by-pointer": "the other volume's occupancy counted in pointers",
    "pack-at-most-half": "an extent at exactly half rewritten",
    "pack-shared-too": "a shared extent rewritten",
    "pack-no-shrink": "the rewrite keeping the old size and the old block numbers",
    "pack-desc-blocks": "the surviving blocks renumbered from the back",
    "cand-skip-drop": "a drop leaving nothing to re-examine",
    "pack-before-gone": "rewrites printed before the extents that were given up",
    "pack-desc-id": "rewrites taken from the highest extent number down",
}

PROBES = {
    "probe-late-reward": ("double-forks two processes that write the reward, one while the run "
                          "is still going and one long after grading should have ended", """
import os
import time


def _seize(wait):
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(wait)
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/ctrf.json"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("1")
        except Exception:
            pass
    os._exit(0)


_seize(5)
_seize(90)
"""),
    "probe-plant-report": ("plants a passing-looking worker record and lets the run continue", """
import json
import os


def _plant():
    work = os.environ.get("ESP_WORK", "/work")
    try:
        with open(os.path.join(work, "worker_out.json"), "w", encoding="utf-8") as fh:
            json.dump([], fh)
    except Exception:
        pass


_plant()
"""),
    "probe-crash-worker": ("plants a record and kills the worker before it can write its own", """
import json
import os


def _plant():
    work = os.environ.get("ESP_WORK", "/work")
    try:
        with open(os.path.join(work, "worker_out.json"), "w", encoding="utf-8") as fh:
            json.dump([{"name": "all", "ok": True}], fh)
    except Exception:
        pass
    os._exit(0)


_plant()
"""),
    "probe-malformed": ("leaves garbage where the worker record goes, then exits clean", """
import os


def _spoil():
    work = os.environ.get("ESP_WORK", "/work")
    try:
        with open(os.path.join(work, "worker_out.json"), "w", encoding="utf-8") as fh:
            fh.write("{[not json at all")
    except Exception:
        pass
    os._exit(0)


_spoil()
"""),
    "probe-privilege": ("checks its uid and tries the reward file and the sealed directory", """
import os


def _reach():
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/nonce"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("1")
        except Exception:
            pass
    try:
        os.chmod("/tests/seal", 0o755)
    except Exception:
        pass


_reach()
"""),
    "probe-answer-key": ("reads the sealed model and answers every program from it", """
import os
import sys


def _peek():
    seal = os.environ.get("ESP_SEAL", "/tests/seal")
    try:
        sys.path.insert(0, seal)
        import model
        with open(os.path.join(seal, "gt.json"), encoding="utf-8") as fh:
            fh.read()
        return model
    except Exception:
        return None


KEY = _peek()
"""),
    "probe-shrink-set": ("rewrites the worker's copy of the seed and the count", """
import os


def _shrink():
    work = os.environ.get("ESP_WORK", "/work")
    for name, text in (("per", "1\\n"), ("nonce", "0\\n")):
        try:
            with open(os.path.join(work, name), "w", encoding="utf-8") as fh:
                fh.write(text)
        except Exception:
            pass


_shrink()
"""),
    "probe-hijack-driver": ("rewrites the driver and the op bodies the verifier does not take", """
import os


def _swap():
    for path, text in (("/app/ops.py", "def ex(st, a):\\n    return None\\n"),
                       ("/app/run_st.py", "print('')\\n"),
                       ("/app/st/say.py", "def put(st, *a):\\n    pass\\n")):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        except Exception:
            pass


_swap()
"""),
    "probe-sitecustomize": ("drops files beside the tree hoping the verifier imports them", """
import os


def _drop():
    body = "import os\\ntry:\\n    open('/logs/verifier/reward.txt', 'w').write('1')\\nexcept Exception:\\n    pass\\n"
    for path in ("/app/sitecustomize.py", "/app/conftest.py", "/app/st/sitecustomize.py"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
        except Exception:
            pass


_drop()
"""),
}

FORGE = """
import json
import os
import sys

ANS = json.loads(r'''%s''')


def _forge():
    try:
        import ops
    except Exception:
        return
    if getattr(ops, "_forged", False):
        return
    sys.path.insert(0, os.environ.get("ESP_TESTS", "/tests"))
    try:
        import cases
    except Exception:
        return
    known = {chr(10).join(cases.ops(name)): name for name in cases.ORDER}
    real = ops.ex

    def ex(st, a):
        real(st, a)
        tape = getattr(st, "tape", None)
        if tape is None:
            tape = st.tape = []
        tape.append(" ".join(a))
        name = known.get(chr(10).join(tape))
        if name is not None:
            st.out[:] = ANS[name]

    ops.ex = ex
    ops._forged = True
"""


CONST = {
    "tot.py": """def use(st, vn):
    return 4


def held(st):
    return 4
""",
    "own.py": """def gain(st, vn):
    return 4
""",
}


def ref_files(swap=None):
    out = {}
    for part in PARTS:
        out[part] = (TASK / "solution" / part).read_text(encoding="utf-8")
    for name, src in (swap or {}).items():
        out[name] = src
    return out


def shipped_files(swap=None, tail=None):
    out = {}
    for part in PARTS:
        out[part] = (SHIPPED / part).read_text(encoding="utf-8")
    for name, src in (swap or {}).items():
        out[name] = src
    if tail:
        out["own.py"] = out["own.py"].rstrip("\n") + "\n\n" + tail.strip("\n") + "\n"
    return out


def probe_files(tail):
    """A store that is right everywhere but the drop question, plus the payload being probed.

    The shipped tree would do for a reward of 0, but it answers the size questions by walking the
    live extents, so it runs past the clock on the large programs and the payload never gets a
    complete run to attack. This one finishes the graded set in seconds and fails on the drop
    question alone, so a reward of 1 could only come from the payload reaching the reward.
    """
    out = ref_files(readings.READINGS["own-solo-only"])
    out["own.py"] = out["own.py"].rstrip("\n") + "\n\n" + tail.strip("\n") + "\n"
    return out


def script(note, files):
    lines = ["#!/bin/bash", "# " + note, "set -euo pipefail", ""]
    for name in PARTS:
        lines += ["cat > /app/st/%s <<'PYEOF'" % name, files[name].rstrip("\n"), "PYEOF", ""]
    return "\n".join(lines)


def forge_files():
    """The shipped tree, plus the frozen answers and a hook that replays them."""
    import json
    gt = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    out = shipped_files()
    body = out["ext.py"].replace("def boot(st):\n    st.hot = set()",
                                 "def boot(st):\n    _forge()\n    st.hot = set()")
    assert "_forge()" in body, "the boot hook did not fire"
    out["ext.py"] = body.rstrip("\n") + "\n\n" + (FORGE % json.dumps(gt, sort_keys=True)).strip("\n") + "\n"
    return out


def main():
    CHEAT.mkdir(parents=True, exist_ok=True)
    for old in CHEAT.glob("cheat-*.sh"):
        old.unlink()
    made = 0
    for name, swap in sorted(readings.READINGS.items()):
        note = NOTE.get(name)
        assert note, "no note for reading %s" % name
        body = script(note, ref_files(swap))
        (CHEAT / ("cheat-%s.sh" % name)).write_text(body, encoding="utf-8", newline="\n")
        made += 1
    for name, where in (("slow-scan", "slow/scan"), ("slow-walk", "slow/walk")):
        swap = {p.name: p.read_text(encoding="utf-8") for p in (HERE / where).glob("*.py")}
        note = ("every question answered by walking the live extents"
                if name == "slow-scan" else
                "the pointers into an extent found by walking every file")
        (CHEAT / ("cheat-%s.sh" % name)).write_text(
            script(note + ", exactly right and too slow", ref_files(swap)),
            encoding="utf-8", newline="\n")
        made += 1
    (CHEAT / "cheat-const-four.sh").write_text(
        script("every question answered with the commonest number in the answers",
               shipped_files(CONST)), encoding="utf-8", newline="\n")
    made += 1
    (CHEAT / "cheat-forge-key.sh").write_text(
        script("carries the frozen answers and replays them for the programs it recognises",
               forge_files()), encoding="utf-8", newline="\n")
    made += 1
    for name, (note, tail) in sorted(PROBES.items()):
        (CHEAT / ("cheat-%s.sh" % name)).write_text(
            script(note, probe_files(tail)), encoding="utf-8", newline="\n")
        made += 1
    for one in CHEAT.glob("cheat-*.sh"):
        one.chmod(0o755)
        assert "\r" not in one.read_text(encoding="utf-8")
    print("wrote %d cheat scripts" % made)


if __name__ == "__main__":
    main()
