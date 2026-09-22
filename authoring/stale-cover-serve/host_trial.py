"""Run the real verifier on the host, at the paths it uses in the container.

Docker Hub's blob host is refused by this session's egress policy, so the two images cannot be
built here and `tools/docker_trial.py` cannot run. This stands in for it and is honest about
what it is: everything except the image build. It lays the shipped tree at /app, the tests at
/tests and the sealed side at /tests/seal, runs the agent script exactly as the platform would
(inside /app, with only the declared artifacts collected afterwards), and then runs the
bundle's own tests/test.sh unmodified - the privilege drop to uid 1002, the 0700 reward
directory, the session and wall clock on the worker, the reaper, and the root-side grader.

What it does not prove: that the images build, and that the base image has the tools the
shipped Dockerfiles install. `tools/imagecheck.py` covers the first of those from the
Dockerfile itself.

It writes absolute paths, so it takes a lock: two copies running at once are one run with the
rows interleaved.

    python -u authoring/stale-cover-serve/host_trial.py oracle
    python -u authoring/stale-cover-serve/host_trial.py nop
    python -u authoring/stale-cover-serve/host_trial.py --all
    python -u authoring/stale-cover-serve/host_trial.py --dir authoring/stale-cover-serve/variants/ok-no-index
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

APP = pathlib.Path("/app")
TESTS = pathlib.Path("/tests")
WORK = pathlib.Path("/work")
PAID = pathlib.Path("/logs/verifier")
LOCK = pathlib.Path("/tmp/scs-host-trial.lock")
ARTS = ["rng/" + p for p in lab.PARTS]


def wipe(path):
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


def stage_tests():
    wipe(TESTS)
    shutil.copytree(lab.TASK / "tests", TESTS)
    subprocess.run(["chmod", "700", str(TESTS / "seal")], check=True)
    subprocess.run(["chmod", "+x", str(TESTS / "test.sh")], check=True)


def stage_app():
    wipe(APP)
    shutil.copytree(lab.SRC, APP)


def agent(script, bundle):
    """Run one agent script inside /app, then keep only the declared artifacts."""
    if script is None:
        return
    env = dict(os.environ)
    done = subprocess.run(["bash", str(script)], cwd=str(APP), env=env,
                          capture_output=True, text=True)
    if done.returncode != 0:
        print("    agent script exited %d: %s"
              % (done.returncode, done.stderr.strip().splitlines()[-1:]))


def collect():
    """What the platform uploads into the verifier: the declared paths and nothing else."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="scs-art-"))
    for rel in ARTS:
        src = APP / rel
        if src.is_file():
            dst = room / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    return room


def verify(artdir):
    """Re-materialise the artifacts at their original paths and run tests/test.sh."""
    wipe(APP)
    (APP / "rng").mkdir(parents=True, exist_ok=True)
    for rel in ARTS:
        src = artdir / rel
        if src.is_file():
            shutil.copy(src, APP / rel)
    wipe(WORK)
    wipe(PAID)
    PAID.parent.mkdir(parents=True, exist_ok=True)
    done = subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True, text=True)
    body = (done.stdout or "") + (done.stderr or "")
    note = WORK / "probe.txt"
    if note.is_file():
        body += "\nprobe said:\n" + note.read_text(encoding="utf-8", errors="replace")
    try:
        reward = int((PAID / "reward.txt").read_text(encoding="utf-8").strip() or 0)
    except Exception:
        reward = 0
    tail = [ln for ln in body.splitlines() if "passed" in ln or "failed" in ln]
    if tail:
        print("    " + tail[-1].strip())
    return reward, body


def trial(name, script, want, bundle=False, show=0):
    print("[%s]" % name)
    stage_tests()
    stage_app()
    agent(script, bundle)
    room = collect()
    try:
        reward, body = verify(room)
    finally:
        shutil.rmtree(room, ignore_errors=True)
    ok = reward == want
    print("    reward=%d expected=%d -> %s" % (reward, want, "PASS" if ok else "FAIL"))
    if show or not ok:
        for line in body.splitlines()[-show or -18:]:
            print("      | %s" % line)
    print("")
    return ok


def probe_run(name, script):
    """One whole verifier run, returning the reward and whatever the probe wrote aside.

    A probe that never fired scores 0 just like one the isolation stopped, so the report
    needs the lines it wrote, not only the number.
    """
    stage_tests()
    stage_app()
    agent(script, False)
    room = collect()
    try:
        wipe(APP)
        (APP / "rng").mkdir(parents=True, exist_ok=True)
        for rel in ARTS:
            src = room / rel
            if src.is_file():
                shutil.copy(src, APP / rel)
        wipe(WORK)
        wipe(PAID)
        PAID.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True, text=True)
        try:
            reward = int((PAID / "reward.txt").read_text(encoding="utf-8").strip() or 0)
        except Exception:
            reward = 0
        note = WORK / "probe.txt"
        said = note.read_text(encoding="utf-8", errors="replace") if note.is_file() else ""
    finally:
        shutil.rmtree(room, ignore_errors=True)
    return reward, said


def from_dir(d):
    lines = ["#!/bin/bash", "set -euo pipefail", ""]
    for part in lab.PARTS:
        one = pathlib.Path(d) / part
        if not one.is_file():
            continue
        lines += ["cat > /app/rng/%s <<'PYEOF'" % part, one.read_text().rstrip("\n"),
                  "PYEOF", ""]
    out = pathlib.Path(tempfile.mkdtemp(prefix="scs-var-")) / "variant.sh"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="?", default="all")
    ap.add_argument("--variants", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dir")
    ap.add_argument("--show", type=int, default=0)
    args = ap.parse_args()

    if LOCK.exists():
        print("another host trial holds %s; refusing to interleave" % LOCK)
        return 2
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    try:
        if args.dir:
            d = pathlib.Path(args.dir)
            return 0 if trial("variant: " + d.name, from_dir(d), 1, show=args.show) else 1
        if args.what == "oracle":
            return 0 if trial("oracle", lab.TASK / "solution" / "solve.sh", 1, bundle=True,
                              show=args.show) else 1
        if args.what == "nop":
            return 0 if trial("nop", None, 0, show=args.show) else 1
        if args.variants:
            res = []
            for d in sorted((HERE / "variants").iterdir()):
                if d.is_dir() and d.name.startswith("ok-"):
                    res.append(trial("variant: " + d.name, from_dir(d), 1))
            print("%d/%d variants scored 1" % (sum(res), len(res)))
            return 0 if all(res) else 1
        if args.all or args.what == "all":
            res = [trial("oracle", lab.TASK / "solution" / "solve.sh", 1, bundle=True),
                   trial("nop", None, 0)]
            for cheat in sorted((lab.TASK / "cheat").glob("*.sh")):
                res.append(trial("cheat: " + cheat.name, cheat, 0))
            print("%d/%d trials behaved as required" % (sum(res), len(res)))
            return 0 if all(res) else 1
        return 0 if trial(args.what, pathlib.Path(args.what), 0, show=args.show) else 1
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
