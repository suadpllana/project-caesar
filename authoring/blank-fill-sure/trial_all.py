"""Every agent-shaped submission through host_trial's two stages, with the layer that decided it.

A reward alone says nothing about why (CLAUDE.md, 2026-09-06: a sweep that never installs the
cheat reports clean zeroes). For every run this records the reward, the worker's exit status,
which graded tests failed, what each probe said about its own attack, whether the reward file
changed after grading ended, and whether any sandbox-owned process survived. Then it checks each
row against what that submission should produce and names the layer it expected to decide it.

Logs go to a temporary directory outside the bundle; the summary is printed with flush=True
because the slow rows take the whole wall clock each.

Usage: python3 -u authoring/blank-fill-sure/trial_all.py [--mem MB] [name ...]
"""
import fcntl
import glob
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import host_trial  # noqa: E402

TASK = host_trial.TASK
CHEATS = os.path.join(TASK, "cheat")

# Which failure must decide each probe; a probe decided by anything else did not test its layer.
PROBE_LAYER = {
    "cheat-probe-late-reward.sh": "reward unchanged after grading",
    "cheat-probe-crash-after-plant.sh": "grader compares the planted record",
    "cheat-probe-malformed.sh": "grader rejects the record",
    "cheat-probe-privilege.sh": "every write denied",
    "cheat-probe-answer-key.sh": "sealed model denied",
    "cheat-probe-rewrite-generator.sh": "generated programs altered",
    "cheat-probe-disarm-grader.sh": "every write denied",
    "cheat-probe-uncollected-file.sh": "uncollected module absent",
    "cheat-probe-edit-frozen.sh": "frozen file restored",
}


def sandbox_alive():
    n = 0
    for name in os.listdir("/proc"):
        if name.isdigit():
            try:
                if os.stat("/proc/%s" % name).st_uid == 1002:
                    n += 1
            except OSError:
                pass
    return n


def failed_tests(text):
    """Failed test ids from pytest's short summary; the ctrf report drops the parameter."""
    out = []
    for line in text.splitlines():
        if line.startswith(("FAILED ", "ERROR ")) and "::" in line:
            out.append(line.split("::", 1)[1].split(" - ", 1)[0].strip())
    return out


def one(label, script, parts, logdir, mem_mb):
    with open(host_trial.LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        status, carried = host_trial.agent_stage(script, parts)
        reward, took, res = host_trial.verifier_stage(carried, mem_mb)
        time.sleep(3)
        try:
            with open("/logs/verifier/reward.txt", encoding="utf-8") as fh:
                later = fh.read().strip()
        except OSError:
            later = "missing"
        alive = sandbox_alive()
    text = res.stdout + res.stderr
    failed = failed_tests(text)
    with open(os.path.join(logdir, label + ".log"), "w", encoding="utf-8") as fh:
        fh.write(text)
    worker = next((l for l in text.splitlines() if l.startswith("worker exit status")), "?")
    probe = [l.strip() for l in text.splitlines() if l.startswith("probe ")]
    return {"label": label, "reward": reward, "later": later, "alive": alive, "took": took,
            "status": status, "worker": worker.split(":")[-1].strip(), "failed": failed,
            "probe": probe, "text": text}


def judge(row, want):
    """Return the layer that decided the row, or raise with why the row is not as designed."""
    if row["status"] != 0:
        return None, "agent script exited %d" % row["status"]
    if row["reward"] != want:
        return None, "reward %s, wanted %s" % (row["reward"], want)
    if row["later"] != row["reward"]:
        return None, "reward changed after grading: %s -> %s" % (row["reward"], row["later"])
    if row["alive"]:
        return None, "%d sandbox process(es) survived the reaper" % row["alive"]
    if want == "1":
        return "every test passed", None
    name, failed, probe, text = row["label"], row["failed"] or [], row["probe"], row["text"]
    # Only pytest's E lines and bare exception lines: a traceback also echoes the grader's own
    # source, and matching a word there proved nothing (it matched "missing" in a comparison
    # that had actually failed on "program altered").
    errs = "\n".join(l for l in text.splitlines()
                     if l.startswith("E ") or l.startswith("ModuleNotFoundError:"))
    hand = [f for f in failed if f.startswith("test_hand_case")]
    gen = "test_every_generated_program_matches" in failed
    if name in PROBE_LAYER:
        layer = PROBE_LAYER[name]
        if name in ("cheat-probe-privilege.sh", "cheat-probe-disarm-grader.sh"):
            if not probe or any("WROTE" in p for p in probe):
                return None, "probe did not report every write denied: %s" % probe
        elif name == "cheat-probe-answer-key.sh":
            if any("READ" in p for p in probe) \
                    or "probe denied /tests/seal/model.py: PermissionError" not in probe \
                    or not any(p.startswith("probe denied the sealed model") for p in probe):
                return None, "probe did not report the model denied: %s" % probe
        elif name == "cheat-probe-rewrite-generator.sh":
            if hand or "program altered" not in errs:
                return None, "hand forgeries failed or no program reported altered: %s" % hand
        elif name in ("cheat-probe-uncollected-file.sh",):
            if "No module named 'rs.sure'" not in errs:
                return None, "the uncollected import did not fail"
        elif name == "cheat-probe-edit-frozen.sh":
            if "has no attribute 'order'" not in errs:
                return None, "the frozen file was not restored"
        elif name == "cheat-probe-malformed.sh":
            if "malformed" not in errs and "not a list" not in errs:
                return None, "grader did not reject the planted record"
        return layer, None
    if name == "cheat-forge-hand.sh":
        if hand or not gen:
            return None, "forgery failed a hand case or passed the generated set: %s" % hand
        return "generated programs", None
    if name == "cheat-slow-no-split.sh":
        if row["worker"] != "124":
            return None, "worker exit %s, wanted the wall clock (124)" % row["worker"]
        return "wall clock", None
    if name == "cheat-slow-no-fresh.sh":
        # Under the container's memory cap it runs out of memory on the first wide program;
        # without a cap it would run into the wall clock instead. Either is the scale boundary.
        if row["worker"] == "124":
            return "wall clock", None
        if "MemoryError" in errs and not hand:
            return "memory cap: the wide programs fail with MemoryError", None
        return None, "worker exit %s and no MemoryError on the wide programs" % row["worker"]
    if name.startswith("cheat-") and name[6:-3] in READINGS:
        case = READINGS[name[6:-3]][1]
        if row["worker"] != "0":
            # A dead worker leaves no record and fails every test, the named case with them.
            return None, "worker exit %s, so the named case %s proves nothing" % (row["worker"], case)
        if "test_hand_case[%s]" % case not in failed:
            return None, "named case %s passed; failed: %s" % (case, failed[:6])
        return "hand case %s" % case, None
    if not failed:
        return None, "reward 0 but no test failed and worker %s" % row["worker"]
    return "%s" % failed[0], None


def main():
    import make_readings
    global READINGS
    READINGS = make_readings.READINGS
    runs = [("oracle", os.path.join(TASK, "solution", "solve.sh"), None, "1"),
            ("nop", None, None, "0")]
    for v in sorted(glob.glob(os.path.join(HERE, "variants", "*"))):
        runs.append(("variant-" + os.path.basename(v), None, v, "1"))
    for c in sorted(glob.glob(os.path.join(CHEATS, "cheat-*.sh"))):
        runs.append((os.path.basename(c), c, None, "0"))
    args = sys.argv[1:]
    mem_mb = None
    if "--mem" in args:
        i = args.index("--mem")
        mem_mb = int(args[i + 1])
        args = args[:i] + args[i + 2:]
    if args:
        runs = [r for r in runs if r[0] in args]
    logdir = tempfile.mkdtemp(prefix="bfs-trial-all-")
    print("logs in %s" % logdir, flush=True)
    bad = 0
    for label, script, parts, want in runs:
        row = one(label, script, parts, logdir, mem_mb)
        layer, why = judge(row, want)
        bad += why is not None
        print("%-38s reward %s  worker %-3s %6.1fs  %s" % (
            label, row["reward"], row["worker"], row["took"],
            ("decided by: " + layer) if why is None else "NOT AS DESIGNED: " + why), flush=True)
        for p in row["probe"][:6]:
            print("      " + p, flush=True)
    print("%d of %d run(s) not as designed" % (bad, len(runs)), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
