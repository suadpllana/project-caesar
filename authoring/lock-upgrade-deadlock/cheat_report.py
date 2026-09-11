"""Every cheat scores 0 - and the layer named for it is the layer that stops it.

A sweep that reads only the reward reports a clean row for a cheat caught by something
unrelated, or for a probe whose attack never fired. So each cheat declares what must catch
it, and the row is red unless that layer is the one that did:

    hand:<case>   the named enumerated program fails on its trace (not on an error)
    orderdep:a|b  a reading whose answer depends on iteration order (the first ring found,
                  from a set of names), so which hand case sees it changes from process to
                  process: the nonce ring family must fail, and the hand cases that fired
                  are reported
    limit         the worker was cut off by the execution limit (exit 124)
    limit+hand:c  the limit cut the worker off on the heavy families, and the reading is
                  also caught by the named hand case when run in-process through readings.py
    nonce         every hand case passes and the nonce population fails
    msg:<text>    a grader message carrying that text (malformed records, altered programs)
    survivors     the reap found a process the service left behind
    records:N     the worker wrote a record for every one of the N graded programs

The three channel probes that leave nothing to read from outside (answer-key, privilege,
reward-now) are judged by the report itself trying the same thing as the sandbox uid, after
test.sh has set the permissions it sets.

Runs through host_trial.py, so it needs root and uid 1002 on this machine.

    python3 authoring/lock-upgrade-deadlock/cheat_report.py [cheat-name ...]
"""
import json
import pathlib
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import host_trial as ht  # noqa: E402

TASK = ht.TASK
TOTAL = 27 + 40 * 10 + 6 * 2

EXPECT = {
    "all-live": "limit",
    "candidate-verify": "limit",
    "per-participant": "limit",
    "whole-rebuild": "limit",
    "cut-early": "hand:cut-late",
    "cut-most": "hand:cut-fewest",
    "cut-no-cancel": "hand:cut-wake",
    "cut-no-wake": "hand:cut-wake",
    "cut-once": "hand:cut-again",
    "cut-one-ring": "orderdep:ring-pair|cut-again",
    "cut-young": "hand:cut-wake",
    "drop-all": "hand:drop-pop",
    "edge-and": "limit+hand:edge-phantom",
    "edge-conflict": "limit+hand:edge-miss",
    "join-rank": "hand:join-pair",
    "pin-bar": "limit+hand:raise-pass",
    "pin-none": "hand:pin-fresh",
    "queue-skip": "hand:queue-stop",
    "raise-ask-mark": "limit+hand:join-pair",
    "raise-ask-order": "hand:raise-order",
    "resume-now": "hand:resume-order",
    "resume-nest": "hand:resume-line",
    "resume-front": "hand:resume-line",
    "self-count": "hand:self-alone",
    "settle-block": "hand:edge-miss",
    "shed-name": "hand:shed-order",
    "probe-answer-key": "sealed",
    "probe-forge-frozen": "nonce",
    "probe-hang": "limit",
    "probe-hijack-tree": "hand:join-pair",
    "probe-malformed": "msg:not a list of lines",
    "probe-plant-exit": "msg:was altered",
    "probe-privilege": "locked",
    "probe-reward-later": "survivors",
    "probe-reward-now": "locked",
    "probe-shrink": "records:%d" % TOTAL,
}

CURRENT = [None]
SANDBOX = ["setpriv", "--reuid=1002", "--regid=1002", "--clear-groups"]


def as_sandbox(code):
    proc = subprocess.run(SANDBOX + ["python3", "-c", code], capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def read_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def observe(stdout):
    """What the verifier's own outputs say caught the submission."""
    gt = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    recs = read_json(ht.WORK / "worker_out.json")
    by = {}
    if isinstance(recs, list):
        for one in recs:
            if isinstance(one, dict) and isinstance(one.get("name"), str):
                by[one["name"]] = one
    hand_fail, hand_err, hand_pass = [], [], []
    for name, want in gt.items():
        one = by.get(name)
        if one is None or one.get("got") is None:
            hand_err.append(name)
        elif one["got"] != want:
            hand_fail.append(name)
        else:
            hand_pass.append(name)
    ctrf = read_json(ht.LOGS / "ctrf.json") or {}
    tests = ctrf.get("results", {}).get("tests", [])
    failed = {}
    for t in tests:
        if t.get("status") != "passed":
            failed.setdefault(t.get("name", "?"), []).append(t.get("trace", "") or "")
    worker = None
    survivors = None
    for ln in stdout.splitlines():
        if ln.startswith("worker exit "):
            worker = int(ln.split()[-1])
        if ln.startswith("survivors "):
            survivors = int(ln.split()[-1])
    return dict(records=len(by), hand_fail=hand_fail, hand_err=hand_err, hand_pass=hand_pass,
                failed=failed, worker=worker, survivors=survivors)


def judge(expect, obs):
    kind, _, arg = expect.partition(":")
    if kind == "limit":
        return obs["worker"] == 124, "worker exit %s" % obs["worker"]
    if kind == "orderdep":
        names = arg.split("|")
        nonce = "test_outputs.py::test_every_nonce_program_matches" in obs["failed"]
        hit = [n for n in names if n in obs["hand_fail"]]
        return nonce, "nonce test %s; hand cases that saw it this run: %s" % (
            "failed" if nonce else "passed", ",".join(hit) or "none")
    if kind == "limit+hand":
        if obs["worker"] != 124:
            return False, "worker exit %s, the limit did not fire" % obs["worker"]
        import readings
        reading = None
        for rn in readings.READINGS:
            if rn == CURRENT[0]:
                reading = rn
        d = pathlib.Path(readings.lab.tempfile.mkdtemp(prefix="crc-reading-"))
        for src in pathlib.Path(readings.REFERENCE).glob("*.py"):
            (d / src.name).write_text(src.read_text())
        for fn, src in readings.READINGS[reading].items():
            (d / fn).write_text(src)
        steps = dict(readings.cases.programs())[arg]
        gt = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
        got = readings.run(d, "\n".join(" ".join(x) for x in steps))
        return got != gt[arg], "limit fired; in-process %s %s" % (
            arg, "differs" if got != gt[arg] else "SAME")
    if kind == "hand":
        return arg in obs["hand_fail"], "hand fail=%s err=%d pass=%d" % (
            ",".join(obs["hand_fail"][:6]) + ("..." if len(obs["hand_fail"]) > 6 else ""),
            len(obs["hand_err"]), len(obs["hand_pass"]))
    if kind == "nonce":
        ok = (not obs["hand_fail"] and not obs["hand_err"]
              and "test_outputs.py::test_every_nonce_program_matches" in obs["failed"])
        return ok, "hand pass=%d, nonce test %s" % (
            len(obs["hand_pass"]),
            "failed" if "test_outputs.py::test_every_nonce_program_matches" in obs["failed"]
            else "passed")
    if kind == "msg":
        hit = any(arg in tr for trs in obs["failed"].values() for tr in trs)
        return hit, "grader message %s" % ("found" if hit else "absent")
    if kind == "survivors":
        return (obs["survivors"] or 0) >= 1, "survivors %s" % obs["survivors"]
    if kind == "records":
        return obs["records"] == int(arg), "records %d" % obs["records"]
    if kind == "sealed":
        rc, out = as_sandbox("open('/tests/seal/gt.json','rb').read(); import os; os.listdir('/tests/seal')")
        return rc != 0 and "Permission" in out, "sandbox read of /tests/seal: %s" % (
            "denied" if rc != 0 else "ALLOWED")
    if kind == "locked":
        rc, out = as_sandbox(
            "import sys\n"
            "for p in ('/logs/verifier/reward.txt','/logs/verifier/per','/tests/gen.py',"
            "'/tests/cases.py'):\n"
            "    try:\n        open(p,'a').write('')\n        print('WROTE', p); sys.exit(3)\n"
            "    except PermissionError:\n        pass\n"
            "print('all denied')")
        return rc == 0 and "all denied" in out, "sandbox writes: %s" % out.splitlines()[-1]
    return False, "unknown layer %s" % expect


def main(argv):
    want = argv or sorted(EXPECT)
    rows = []
    for name in want:
        CURRENT[0] = name
        sh = TASK / "cheat" / ("cheat-%s.sh" % name)
        t0 = time.time()
        art = ht.agent_stage(sh, False)
        reward, proc = ht.verifier_stage(art)
        shutil.rmtree(art, ignore_errors=True)
        obs = observe(proc.stdout)
        ok, why = judge(EXPECT[name], obs)
        ok = ok and reward == 0
        rows.append(ok)
        print("%-22s reward=%d %-24s %-4s %s  (%.0fs)" % (
            name, reward, EXPECT[name], "ok" if ok else "FAIL", why, time.time() - t0),
            flush=True)
        if not ok:
            print("    " + "\n    ".join(proc.stdout.splitlines()[-12:]), flush=True)
    left = subprocess.run(["pgrep", "-u", "1002"], capture_output=True, text=True).stdout.split()
    if left:
        print("processes still running as uid 1002 after the run: %s" % left)
        rows.append(False)
    print("%d/%d cheats caught by the layer named for them" % (sum(rows), len(rows)))
    return 0 if all(rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
