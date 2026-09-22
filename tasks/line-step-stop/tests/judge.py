"""Trusted grader for line-step-stop. Runs as root, before the pytest report is written.

What it does, in order:

1. Re-plays every small frozen session (the small samples, the enumerated cases and the
   fences) through the sealed model and requires the frozen lines back. A model that
   drifted after the lines were frozen cannot redefine what correct means.
2. Plays the frozen sessions - the four samples the agent was given, the enumerated cases,
   the fences, the heavy sessions - through the submitted debugger, stopping at the first
   one that fails.
3. Builds the nonce population - sessions from every family of the sealed generator, seeded
   from os.urandom after the agent's container is gone, expected lines from the model - and
   plays it the same way.
   Every session runs like this:
     - the target runs under its own uid (TGT_UID) with the tape on its stdin; nothing else
       ever holds the tape;
     - the debugger runs under another uid (DBG_UID) in a pristine tree with only the three
       declared files laid over it, in its own session, with only a socket to the target and
       a pipe for the lines the session driver prints;
     - after each session every process of both uids is killed.
   The whole graded set shares one wall clock (LIMIT seconds), counted from each debugger
   process's start to its exit; a session that would run past what is left is killed.
4. Writes the verdict to a root-only directory the debugger is never told about.

The reward is not written here; test.sh writes it from this verdict and pytest's status.
"""

import json
import os
import pwd
import random
import shutil
import signal
import socket
import subprocess
import sys
import time

SEAL = "/tests/seal"
BASE = "/tests/base"
WORK = "/work"
APP_IN = "/app/dbg"
VERDICT_DIR = "/var/lib/judge"
ARTIFACTS = ("marks.py", "frames.py", "steps.py")
LIMIT = 300.0            # seconds for the whole graded set; stated in instruction.md
PER_FAMILY = 34          # nonce sessions per generator family

DBG = pwd.getpwnam("dbgr")
TGT = pwd.getpwnam("tgtr")
DBG_UID = DBG.pw_uid
TGT_UID = TGT.pw_uid

sys.path.insert(0, SEAL)
import forge  # noqa: E402
import model  # noqa: E402


def verdict(obj):
    os.makedirs(VERDICT_DIR, mode=0o700, exist_ok=True)
    os.chmod(VERDICT_DIR, 0o700)
    tmp = os.path.join(VERDICT_DIR, "verdict.tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, os.path.join(VERDICT_DIR, "verdict.json"))


def drop(user):
    def go():
        os.setgroups([])
        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)
    return go


def reap(uid):
    """Kill every process owned by uid (double-forked survivors included)."""
    for _ in range(3):
        found = False
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                if os.stat("/proc/" + pid).st_uid == uid:
                    os.kill(int(pid), signal.SIGKILL)
                    found = True
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                pass
        if not found:
            return
        time.sleep(0.05)


def stage_tree():
    """A pristine tree with only the declared files laid over it, readable, not writable."""
    app = os.path.join(WORK, "app")
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK, mode=0o755)
    shutil.copytree(BASE, app)
    missing = []
    for f in ARTIFACTS:
        src = os.path.join(APP_IN, f)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(app, "dbg", f))
        else:
            missing.append(f)
    for root, dirs, files in os.walk(WORK):
        os.chmod(root, 0o755)
        for f in files:
            os.chmod(os.path.join(root, f), 0o644)
    return app, missing


def play(app, idx, s, budget):
    """Run one session through the submitted debugger. Returns (lines, seconds, status)."""
    d = os.path.join(WORK, "s%04d" % idx)
    os.makedirs(d, mode=0o755)
    with open(os.path.join(d, "p.img"), "w") as f:
        f.write(s["image"])
    with open(os.path.join(d, "p.cmd"), "w") as f:
        f.write("\n".join(s["cmds"]) + "\n")
    for f in ("p.img", "p.cmd"):
        os.chmod(os.path.join(d, f), 0o644)
    ours, theirs = socket.socketpair()
    out_r, out_w = os.pipe()
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
           "HOME": "/tmp", "LANG": "C.UTF-8"}
    tgt = subprocess.Popen(
        [sys.executable, os.path.join(app, "tgt", "serve.py"), os.path.join(d, "p.img"),
         str(theirs.fileno())],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        pass_fds=(theirs.fileno(),), preexec_fn=drop(TGT), start_new_session=True,
        env=env, cwd="/")
    tgt.stdin.write((" ".join(str(v) for v in s["tape"]) + "\n").encode())
    tgt.stdin.close()
    theirs.close()
    t0 = time.monotonic()
    dbg = subprocess.Popen(
        [sys.executable, "/tests/probe.py", app, d, str(ours.fileno()), str(out_w)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        pass_fds=(ours.fileno(), out_w), preexec_fn=drop(DBG), start_new_session=True,
        env=env, cwd="/tmp")
    ours.close()
    os.close(out_w)
    chunks = []
    status = "ok"
    deadline = t0 + max(budget, 0.0)
    os.set_blocking(out_r, False)
    while True:
        try:
            b = os.read(out_r, 65536)
            if b:
                chunks.append(b)
                if sum(len(c) for c in chunks) > 4000000:
                    status = "flood"
                    break
                continue
            if b == b"":
                # The driver's pipe is closed; let the process finish exiting, within budget.
                try:
                    dbg.wait(timeout=max(deadline - time.monotonic(), 0.0))
                except subprocess.TimeoutExpired:
                    status = "limit"
                break
        except BlockingIOError:
            pass
        if dbg.poll() is not None:
            try:
                while True:
                    b = os.read(out_r, 65536)
                    if not b:
                        break
                    chunks.append(b)
            except BlockingIOError:
                pass
            break
        if time.monotonic() > deadline:
            status = "limit"
            break
        time.sleep(0.002)
    secs = time.monotonic() - t0
    for p in (dbg, tgt):
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    reap(DBG_UID)
    reap(TGT_UID)
    for p in (dbg, tgt):
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
    os.close(out_r)
    try:
        text = b"".join(chunks).decode("utf-8", "replace")
    except Exception:
        text = ""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    shutil.rmtree(d, ignore_errors=True)
    return lines, secs, status


def run_group(app, graded, result, base):
    """Play sessions in order; stop at the first one that fails. Returns True if all pass."""
    for k, (group, s) in enumerate(graded):
        try:
            lines, secs, status = play(app, base + k, s, LIMIT - result["spent"])
        except Exception as e:  # anything unexpected is a failure, never a pass
            lines, secs, status = [], 0.0, "judge error %r" % (e,)
        result["spent"] = round(result["spent"] + secs, 3)
        if status != "ok" or lines != s["want"]:
            first = next((j for j, (a, b) in enumerate(zip(s["want"], lines)) if a != b),
                         min(len(lines), len(s["want"])))
            result["failed"] = {"group": group, "name": s.get("name", str(base + k)),
                                "status": status, "line": first, "secs": round(secs, 3),
                                "want": s["want"][first] if first < len(s["want"]) else None,
                                "got": lines[first] if first < len(lines) else None}
            return False
        result["passed"][group] += 1
    return True


def main():
    result = {"ok": False, "stage": "start"}
    verdict(result)
    with open(os.path.join(SEAL, "gt.json")) as f:
        frozen = json.load(f)

    # 0. The frozen sessions are exactly the ones tests/cases.py names and describes.
    sys.path.insert(0, "/tests")
    import cases
    named = {"samples": set(cases.SAMPLES), "cases": set(cases.CASES), "fences": set(cases.FENCES),
             "heavy": set(cases.HEAVY)}
    held = {"samples": {s["name"] for s in frozen["samples"]},
            "cases": {s["reading"] for s in frozen["cases"]},
            "fences": {s["name"] for s in frozen["fences"]}, "heavy": {s["name"] for s in frozen["heavy"]}}
    if named != held:
        result["stage"] = "cases"
        verdict(result)
        return

    # 1. The model must reproduce every small frozen session.
    drift = []
    for s in frozen["samples"] + frozen["cases"] + frozen["fences"]:
        if s.get("recheck") and model.play(s["image"], s["tape"], s["cmds"]) != s["want"]:
            drift.append(s["name"])
    result["model_drift"] = drift
    if drift:
        result["stage"] = "model"
        verdict(result)
        return

    # 2. Frozen sessions first (cases, fences, heavy): a run that fails here never pays for
    #    generating the nonce population.
    app, missing = stage_tree()
    result["missing"] = missing
    if missing:
        result["stage"] = "artifacts"
        verdict(result)
        return
    frozen_graded = ([("sample", s) for s in frozen["samples"]] + [("case", s) for s in frozen["cases"]]
                     + [("fence", s) for s in frozen["fences"]] + [("heavy", s) for s in frozen["heavy"]])
    result["counts"] = {"sample": len(frozen["samples"]), "case": len(frozen["cases"]),
                        "fence": len(frozen["fences"]), "heavy": len(frozen["heavy"]),
                        "nonce": len(forge.FAMILIES) * PER_FAMILY}
    result["passed"] = {"sample": 0, "case": 0, "fence": 0, "heavy": 0, "nonce": 0}
    result["spent"] = 0.0
    result["limit"] = LIMIT
    result["stage"] = "play"
    verdict(result)
    if not run_group(app, frozen_graded, result, 0):
        result["stage"] = "done"
        verdict(result)
        return

    # 3. The nonce population, seeded after the agent's container is gone.
    rng = random.Random(int.from_bytes(os.urandom(8), "big"))
    nonce = []
    for fam in sorted(forge.FAMILIES):
        for k in range(PER_FAMILY):
            s = forge.session(fam, rng)
            s["name"] = "%s-%02d" % (fam, k)
            nonce.append(("nonce", s))
    run_group(app, nonce, result, len(frozen_graded))
    result["ok"] = ("failed" not in result and result["spent"] <= LIMIT
                    and all(result["passed"][g] == result["counts"][g] for g in result["passed"]))
    result["stage"] = "done"
    verdict(result)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        verdict({"ok": False, "stage": "crash", "error": repr(e)})
        raise
