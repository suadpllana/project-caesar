#!/usr/bin/env python3
"""Run every cheat through the host trial and record what caught it.

The reward alone is not evidence: a cheat can score 0 because it crashed on its own, which
proves nothing about the verifier. So this records the tests that failed as well, and for the
attestation probes what the payload printed - a probe that never reached its target is a probe
that tested nothing.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
HERE = pathlib.Path(__file__).resolve().parent
TRIAL = HERE / "host_trial.py"
OUT = HERE / "cheat_report.json"

FAIL = re.compile(r"(?:FAILED|ERROR)\s+\S*test_outputs\.py::(\S+)")


def run(args):
    p = subprocess.run([sys.executable, str(TRIAL)] + args, cwd=str(ROOT),
                       capture_output=True, text=True)
    text = p.stdout + p.stderr
    m = re.search(r"reward (\S+)", text)
    return (m.group(1) if m else "?"), text


def main():
    only = sys.argv[1:]
    rows = []
    names = sorted(p.name for p in (TASK / "cheat").iterdir() if p.suffix == ".sh")
    if only:
        names = [n for n in names if any(o in n for o in only)]
    for name in names:
        reward, text = run(["cheat", "--cheat", str(TASK / "cheat" / name)])
        caught = sorted(set(FAIL.findall(text)))
        note = [l for l in text.splitlines()
                if l.startswith(("uid ", "seal ", "model ", "answers ", "shrank ", "planted ",
                                 "WROTE ", "leaving ")) or " PermissionError" in l
                or " FileNotFoundError" in l or " IsADirectoryError" in l]
        rows.append({"cheat": name, "reward": reward, "caught": caught[:6], "says": note[:8]})
        flag = "" if reward == "0" else "   <-- SCORED %s" % reward
        print("%-34s reward %s  %s%s" % (name, reward, ", ".join(caught[:3]) or "-", flag),
              flush=True)
        for line in note[:6]:
            print("      %s" % line, flush=True)
    OUT.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8", newline="\n")
    bad = [r["cheat"] for r in rows if r["reward"] != "0"]
    print("\n%d cheats, %d scored non-zero%s" % (len(rows), len(bad),
                                                 (": %s" % bad) if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
