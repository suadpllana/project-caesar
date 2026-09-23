#!/usr/bin/env python3
"""Every cheat scores 0 - and the layer named for it is the layer that stops it.

A sweep that reads only the reward reports a clean row for a cheat that was never installed, or
for one caught by something unrelated (CLAUDE.md, token-seam-emit). So each cheat declares what
must catch it, and this checks that layer:

  a hand case       the worker and the grader run host-side, and the named test must fail
  limit             the worker must be cut off by the execution limit before it writes a record
  worker            the worker must die on the named error before it writes a record
  trial             the probe needs the second uid and the root-owned reward channel, so it is
                    judged in the two containers (--trial): its own report of what its attempt
                    came to must name the lock, and for the two probes that could have scored,
                    the same payload with the locks taken off must score 1

It also prints how much of the graded set each cheat still gets right, which is how the
shortcuts are measured. The submitted files are lifted out of each cheat's heredocs rather than
by running it against /app, so the host pass is hermetic.

    python3 -u authoring/live-region-reader/cheat_report.py
    python3 -u authoring/live-region-reader/cheat_report.py --trial
"""
import os
import pathlib
import re
import secrets
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "live-region-reader"
TESTS = TASK / "tests"
CHEATS = TASK / "cheat"

LIMIT = 60
PER = 30
BLOCK = re.compile(r"cat > /app/sr/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)


def hand(case):
    return "test_hand_case[%s]" % case


NONCE = "test_every_nonce_program_matches"
POPULATION = None

EXPECT = {
    "absorb-keeps-carry": hand("absorb-carried"),
    "age-resets-on-edit": hand("edit-keeps-age"),
    "anchor-follows-move": hand("removal-last-believed"),
    "assertive-cuts-assertive": hand("alert-waits"),
    "atomic-false-ignored": hand("atomic-false-stops"),
    "atomic-region-only": hand("atomic-inner"),
    "belief-by-node": hand("move-across"),
    "busy-above-region": hand("busy-above-ignored"),
    "busy-any-value": hand("busy-false-releases"),
    "busy-region-only": hand("busy-inner"),
    "cut-to-back": hand("cut-keeps-age"),
    "cut-when-held": hand("held-alert-no-cut"),
    "empty-says": hand("empty-unit"),
    "finish-after-cut": hand("finish-before-cut"),
    "hidden-false-reveals": hand("hidden-false-stays"),
    "hidden-false-shows": hand("hidden-any-value"),
    "irrelevant-kept": hand("relevance-absorbs"),
    "learn-at-start": hand("cut-hands-back"),
    "off-transparent": hand("off-stops"),
    "oldest-across-classes": hand("assertive-first"),
    "queue-strings": hand("stale-in-line"),
    "region-hidden-voiced": hand("region-hidden-silent"),
    "relevant-bogus-empty": hand("relevant-bogus"),
    "relevant-nearest": hand("relevant-region-only"),
    "removal-at-region": hand("removal-held-anchor"),
    "silent-kept": hand("off-absorbs"),
    "tie-doc-order": hand("tie-node-id"),
    "timing-plus-one": hand("timing-words"),
    "unit-carries-held": hand("unit-leaves-held"),
    "slow-page": "limit",
    "slow-line": "limit",
    "const-silent": hand("plain-once"),
    "pos-record-order": hand("stale-in-line"),
    "replay-example": hand("plain-once"),
    "forge-hand": NONCE,
    "probe-plant-report": hand("tiny-example"),
    "probe-crash-worker": hand("tiny-example"),
    "probe-malformed": ("error", "worker produced no readable output"),
    "probe-uncollected-file": ("worker", "No module named 'sr.helper'"),
    "probe-answer-key": "trial",
    "probe-reward-direct": "trial",
    "probe-late-reward": "trial",
    "probe-privilege": "trial",
    "probe-disarm-grader": "trial",
    "probe-shrink-set": "trial",
}

# What each probe must say about its own attempt in the two-container run. Every pattern must
# appear in its report line, and nothing in SUCCESS may.
TRIAL = {
    "probe-answer-key": ("model ModuleNotFoundError", "gt.json PermissionError"),
    "probe-reward-direct": ("PermissionError",),
    "probe-late-reward": ("survivor running, PermissionError",),
    "probe-privilege": ("uid 1002", "/logs/verifier/reward.txt PermissionError",
                        "/tests/seal/gt.json PermissionError"),
    "probe-disarm-grader": ("PermissionError",),
    "probe-shrink-set": ("/tests/gen.py PermissionError", "/tests/cases.py PermissionError",
                         "/logs/verifier/per PermissionError"),
}
SUCCESS = ("imported", " read", "wrote", "appended", "rewrote", "rewritten")
# With the privilege drop and the seal lock taken off, these would have scored 1.
UNLOCKED = {
    "probe-answer-key": "model imported, gt.json read",
    "probe-disarm-grader": "rewrote the grader",
}


def submitted(sh):
    """The files the cheat leaves under /app/sr, lifted out of its heredocs."""
    out = pathlib.Path(tempfile.mkdtemp(prefix="lrr-sub-"))
    for name, src in BLOCK.findall(sh.read_text(encoding="utf-8")):
        (out / name).write_text(src + "\n", encoding="utf-8")
    return out


def host_run(sub):
    """Worker then grader, host-side, every path pointed at a scratch directory."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="lrr-run-"))
    work, logs = room / "work", room / "logs"
    work.mkdir()
    logs.mkdir()
    nonce = secrets.token_hex(16)
    for d in (work, logs):
        (d / "nonce").write_text(nonce + "\n", encoding="utf-8")
        (d / "per").write_text("%d\n" % PER, encoding="utf-8")
    env = dict(os.environ)
    env.update({"LRR_TESTS": str(TESTS), "LRR_WORK": str(work), "LRR_LOGS": str(logs),
                "LRR_SEAL": str(TESTS / "seal"), "LRR_SUB": str(sub),
                "PYTHONDONTWRITEBYTECODE": "1", "COLUMNS": "4000"})
    try:
        w = subprocess.run([sys.executable, str(TESTS / "worker.py"),
                            "--out", str(work / "worker_out.json")],
                           env=env, capture_output=True, text=True, timeout=LIMIT)
        rc, err = w.returncode, w.stderr
    except subprocess.TimeoutExpired:
        rc, err = 124, ""
    g = subprocess.run([sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"),
                        "-p", "no:cacheprovider", "-q", "--tb=no", "-rfE"],
                       cwd=str(room), env=env, capture_output=True, text=True, timeout=1800)
    shutil.rmtree(room, ignore_errors=True)
    failed, errors = [], []
    for line in g.stdout.splitlines():
        m = re.match(r"^(FAILED|ERROR) \S*::(\S+)", line.strip())
        if m:
            (failed if m.group(1) == "FAILED" else errors).append(m.group(2))
    m = re.search(r"(\d+) of (\d+) nonce pages wrong", g.stdout)
    wrong, total = (int(m.group(1)), int(m.group(2))) if m else (0, POPULATION)
    return {"rc": rc, "err": err, "failed": failed, "errors": errors, "out": g.stdout,
            "graded": g.returncode, "wrong": wrong, "total": total}


def judge(name, want, r):
    if want == "limit":
        return r["rc"] == 124, "worker rc=%d, %s" % (
            r["rc"], "cut off by the limit" if r["rc"] == 124 else "NOT CUT OFF")
    if isinstance(want, tuple) and want[0] == "worker":
        ok = r["rc"] not in (0, 124) and want[1] in r["err"] and r["graded"] != 0
        return ok, "worker rc=%d, %s" % (r["rc"], "died on %s" % want[1] if ok else
                                         "DID NOT DIE ON %s" % want[1])
    if isinstance(want, tuple) and want[0] == "error":
        ok = r["graded"] != 0 and want[1] in r["out"] and not r["failed"]
        return ok, ("every test errors: %s" % want[1]) if ok else "NOT REJECTED AS UNREADABLE"
    ok = r["graded"] != 0 and want in r["failed"]
    return ok, ("caught by %s" % want) if ok else "NOT CAUGHT BY %s (fails %s)" % (
        want, ", ".join(r["failed"][:3]) or "nothing")


def host_pass():
    global POPULATION
    import cases  # noqa: E402
    import gen  # noqa: E402
    POPULATION = len(gen.programs("size", PER))
    hand_total = len(cases.ORDER)
    bad = 0
    names = sorted(sh.stem[len("cheat-"):] for sh in CHEATS.glob("cheat-*.sh"))
    missing = sorted(set(names) - set(EXPECT))
    for name in missing:
        print("   %-26s NO EXPECTATION - add it to EXPECT" % name)
        bad += 1
    print("   %-26s %-12s %-14s %s" % ("cheat", "hand right", "nonce right", "layer"))
    for name in names:
        want = EXPECT.get(name)
        if want is None or want == "trial":
            continue
        r = host_run(submitted(CHEATS / ("cheat-%s.sh" % name)))
        ok, why = judge(name, want, r)
        bad += 0 if ok else 1
        hand_bad = sum(1 for f in r["failed"] if f.startswith("test_hand_case["))
        if r["errors"] or r["rc"] == 124:
            right = "-"
            nonce = "-"
        else:
            right = "%d/%d" % (hand_total - hand_bad, hand_total)
            nonce = "%d/%d" % (r["total"] - r["wrong"], r["total"])
        print("   %-26s %-12s %-14s %s" % (name, right, nonce, why), flush=True)
    return bad


def ran(summary):
    """How many tests the grader's closing summary line accounts for."""
    if not summary:
        return 0
    return sum(int(n) for n in re.findall(r"(\d+) (?:passed|failed|errors?)\b", summary[-1]))


def trial_pass():
    import cases  # noqa: E402
    sys.path.insert(0, str(ROOT / "tools"))
    import docker_trial
    t = docker_trial.Trial("live-region-reader")
    if t.build() != 0:
        print("   image build failed")
        return 1
    loose = (TESTS / "test.sh").read_text(encoding="utf-8")
    for old in ('setpriv --reuid="${READER_UID}" --regid="${READER_UID}" --clear-groups \\\n    ',
                "chmod 700 /tests/seal\n"):
        if loose.count(old) != 1:
            print("   cannot build the unlocked control: %r not found once" % old[:40])
            return 1
        loose = loose.replace(old, "")
    ctl = pathlib.Path(tempfile.mkdtemp(prefix="lrr-ctl-"))
    (ctl / "test.sh").write_text(loose, encoding="utf-8", newline="\n")

    def verify(art, script):
        parents = sorted({str(pathlib.Path("/app") / a).rsplit("/", 1)[0] for a in t.arts})
        cmd = ("mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; mkdir -p /logs/verifier ; "
               "bash %s > /tmp/v.log 2>&1 ; echo REWARD=$(cat /logs/verifier/reward.txt) ; "
               "cat /tmp/v.log") % (" ".join(parents), script)
        p = subprocess.run(["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % art,
                            "-v", "%s:/ctl:ro" % ctl, t.test_img, "bash", "-c", cmd],
                           capture_output=True, text=True)
        m = re.search(r"^REWARD=(\d)", p.stdout, re.M)
        return (int(m.group(1)) if m else -1), p.stdout

    bad = 0
    for name in sorted(TRIAL):
        # mkdtemp is 0700, and `cp -a /artifacts/. /app/` carries that mode onto /app, which
        # locks the sandbox uid out of the submission before anything is graded. docker_trial
        # uses a fresh subdirectory for the same reason.
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="lrr-art-"))
        art = tmp / "art"
        t.agent_run(CHEATS / ("cheat-%s.sh" % name), art)
        reward, log = verify(art, "/tests/test.sh")
        said = [ln for ln in log.splitlines() if ln.startswith("probe ")]
        reaped = re.search(r"survivors killed: (\d+)", log)
        summary = [ln for ln in log.splitlines() if re.search(r"\d+ (passed|failed)", ln)]
        problems = []
        if reward != 0:
            problems.append("reward %d" % reward)
        if len(said) != 1:
            problems.append("%d report lines" % len(said))
        line = said[0] if said else ""
        problems += ["missing %r" % p for p in TRIAL[name] if p not in line]
        problems += ["success %r" % s for s in SUCCESS if s in line]
        if name == "probe-late-reward" and not (reaped and int(reaped.group(1)) >= 1):
            problems.append("no survivor reaped")
        if ran(summary) != len(cases.ORDER) + 3:
            problems.append("grader ran %d tests" % ran(summary))
        control = ""
        if name in UNLOCKED:
            r2, log2 = verify(art, "/ctl/test.sh")
            said2 = [ln for ln in log2.splitlines() if ln.startswith("probe ")]
            if r2 != 1 or not said2 or UNLOCKED[name] not in said2[0]:
                problems.append("unlocked control scored %d (%s)" % (r2, said2[:1]))
            else:
                control = "; unlocked control scores 1"
        shutil.rmtree(tmp, ignore_errors=True)
        verdict = "stopped: " + line[len("probe "):] + control if not problems else \
            "WRONG LAYER: " + "; ".join(problems)
        if reaped and name == "probe-late-reward":
            verdict += "; survivors killed %s" % reaped.group(1)
        print("   %-26s %s" % (name, verdict), flush=True)
        bad += 1 if problems else 0
    shutil.rmtree(ctl, ignore_errors=True)
    return bad


def main(argv):
    sys.path.insert(0, str(TESTS))
    if "--trial" in argv:
        print("== live-region-reader probes, two containers")
        bad = trial_pass()
    else:
        print("== live-region-reader cheat layers, host-side (%d s limit, %d per family)"
              % (LIMIT, PER))
        bad = host_pass()
    print("   %d findings" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
