#!/usr/bin/env python3
"""Every cheat scores 0 - and the layer named for it is the layer that stops it. Never ships.

A sweep that reads only the reward reports a clean row for a cheat that was never installed, or
one caught by something unrelated (CLAUDE.md, token-seam-emit: assert the layer, never just the
reward). So each cheat declares what must catch it:

  * a named enumerated case (`test_hand_case[...]`)  - the wrong-reading cheats;
  * the enumerated grading at large (`test_hand_case`) - the dumb shortcuts;
  * the generated population (`test_every_small_program_matches`) - the forgery that carries the
    frozen answers, which passes every enumerated case and no generated one;
  * the wall clock (`limit`) - the exact-but-slow families, timed by scale.py / host_trial;
  * the two-container privilege drop (`trial`) - the probes, run by host_trial.py --all.

The four submitted files are lifted straight out of each cheat's heredocs, so this is hermetic
and runs beside anything else. It grades on the enumerated programs and a small generated
population; the scale families it leaves to the timing evidence, since a full relayout on the
scale programs is minutes, not a unit test.

    python3 cheat_report.py
"""
import hashlib
import json
import os
import pathlib
import re
import secrets
import subprocess
import sys
import tempfile

import lab
import readings

TESTS = lab.TASK / "tests"
CHEATS = lab.TASK / "cheat"
BLOCK = re.compile(r"cat > /app/view/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)

SHORTCUTS = {"const-lines", "pos-first-box", "replay-small"}
SLOW = {"full-relayout": 489, "scan-headers": 471}
PROBES = {"probe-answer-key", "probe-privilege", "probe-late-reward", "probe-forge-report",
          "probe-shrink-set", "probe-crash-worker"}


def expectation(name):
    if name in readings.READINGS:
        return "test_hand_case[%s]" % readings.CASE[name]
    if name in SHORTCUTS:
        return "test_hand_case"
    if name == "forge-from-truth":
        return "test_every_small_program_matches"
    if name in SLOW:
        return "limit"
    if name in PROBES:
        return "trial"
    return None


def submitted(sh):
    out = pathlib.Path(tempfile.mkdtemp(prefix="abs-cheat-sub-"))
    for part, src in BLOCK.findall(sh.read_text(encoding="utf-8")):
        (out / part).write_text(src + "\n", encoding="utf-8")
    return out


def population():
    """hand + a small generated population, written once and shared. No scale families here."""
    cases, gen, _model = lab.sealed()
    seed = secrets.token_hex(8)
    progs = [{"fam": "hand", "name": n, "text": "\n".join(cases.prog(n)) + "\n"}
             for n in cases.ORDER]
    progs += [{"fam": f, "name": n, "text": "\n".join(l) + "\n"}
              for f, n, l in gen.programs(seed, 30, small_only=True)]
    room = pathlib.Path(tempfile.mkdtemp(prefix="abs-cheat-pop-"))
    path = room / "progs.json"
    path.write_text(json.dumps(progs), encoding="utf-8", newline="\n")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return path, sha


def run(sub, progs, sha):
    room = pathlib.Path(tempfile.mkdtemp(prefix="abs-cheat-run-"))
    work, logs, run_dir = room / "work", room / "logs", room / "run"
    for d in (work, logs, run_dir):
        d.mkdir()
    (logs / "progs.sha").write_text(sha, encoding="utf-8")
    env = dict(os.environ, ABS_TESTS=str(TESTS), ABS_WORK=str(work), ABS_SUB=str(sub),
               ABS_SEAL=str(TESTS / "seal"), ABS_RUN=str(run_dir), ABS_LOGS=str(logs),
               PYTHONDONTWRITEBYTECODE="1")
    # the grader reads PROGS from ABS_RUN/progs.json; point both halves at the shared file
    (run_dir / "progs.json").write_bytes(progs.read_bytes())
    worker_rc = 0
    try:
        w = subprocess.run([sys.executable, str(TESTS / "worker.py"),
                            "--progs", str(progs), "--out", str(work / "worker_out.json")],
                           env=env, capture_output=True, text=True, timeout=120)
        worker_rc = w.returncode
    except subprocess.TimeoutExpired:
        worker_rc = 124
    g = subprocess.run([sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"),
                        "-p", "no:cacheprovider", "-q", "--tb=no", "-rfE"],
                       env=env, capture_output=True, text=True, timeout=1800)
    bad = set()
    for line in g.stdout.splitlines():
        m = re.match(r"^(FAILED|ERROR) \S*::(\S+)", line.strip())
        if m:
            bad.add(m.group(2))
    return worker_rc, bad, g.returncode


def main():
    progs, sha = population()
    rows, wrong = [], 0
    for sh in sorted(CHEATS.glob("cheat-*.sh")):
        name = sh.stem[len("cheat-"):]
        want = expectation(name)
        if want is None:
            rows.append("   %-22s NO EXPECTATION - add it" % name)
            wrong += 1
            continue
        if want == "limit":
            rows.append("   %-22s cut off by the 90 s clock (scale timing: %d s > 90 s)"
                        % (name, SLOW[name]))
            continue
        if want == "trial":
            rows.append("   %-22s left to the two-container trial (host_trial.py --all)" % name)
            continue
        sub = submitted(sh)
        rc, bad, graded = run(sub, progs, sha)
        if name == "forge-from-truth":
            hand_fail = any(b.startswith("test_hand_case") for b in bad)
            ok = graded != 0 and want in bad and not hand_fail
            rows.append("   %-22s %s (enumerated all pass: %s; %s failed)"
                        % (name, "caught" if ok else "NOT AS EXPECTED",
                           not hand_fail, want if want in bad else "population did not fail"))
        else:
            ok = graded != 0 and any(b == want or b.startswith(want + "[") for b in bad)
            hits = sorted(b for b in bad if b == want or b.startswith(want + "["))
            hit = ", ".join(hits[:3]) if hits else (", ".join(sorted(bad)[:2]) or "nothing failed")
            rows.append("   %-22s %s <- %s" % (name, "caught" if ok else "NOT CAUGHT BY " + want, hit))
        if not ok:
            wrong += 1
    print("== anchor-band-settle cheat layers")
    for r in rows:
        print(r)
    print("   %d flagged; %d cheats accounted for" % (wrong, len(rows)))
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
