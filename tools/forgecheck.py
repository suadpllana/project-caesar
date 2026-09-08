#!/usr/bin/env python3
"""Does the verifier demand evidence, or does it grade a report?

The anti-cheat gate rejected delta-view-retraction on 2026-08-13 because a submission that
did no work at all could pass. Nothing was broken out of: the run is sandboxed and the
ground truth is root-only. The hole was narrower and worse - every number the verifier
compared came out of the process that executed the agent's file, so a file that hijacked
the driver's report and returned the right answers was indistinguishable from one that
computed them. Sealing the ground truth does not help, because the adversary the gate
models has already read it.

This gate asks two mechanical questions of a task:

  1. Does cheat/ contain a probe that was generated from tests/gt.json - that is, a cheat
     that is handed every answer? A cheat suite made only of wrong implementations tests
     the problem. It does not test the verifier.
  2. Does every cheat still score 0 through the task's own emulation?

A task that passes has been shown to reject a submission holding the complete answer key.
A task with no such cheat is not proved vulnerable by this script; it is unmeasured, which
is the state delta-view-retraction was in when it was submitted.

Usage:
    python3 tools/forgecheck.py <slug>
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def answer_slices(gt_text: str, n: int = 12) -> list[str]:
    """The same idea, over the answers alone.

    Keys are names the author chose - "requeue-joins-the-tail" - and a cheat that carries
    the answers has no reason to contain them, so a bundle whose only long tokens are its
    keys reports no carrier however real its forgery probe is. Measured 2026-09-08 on a
    bundle whose probe replays 24 of 25 frozen traces and scores 0.
    """
    leaves = [chunk for chunk in gt_leaves(json.loads(gt_text)) if len(chunk) >= 24]
    return leaves[:n]


def gt_leaves(data) -> list[str]:
    """Every value in the ground truth, with the keys left out.

    Keys are names the author chose - "requeue-joins-the-tail" - and a cheat that
    carries the answers has no reason to contain them. Matching on them measures
    whether the cheat was written against the same case list, not whether it holds
    the answers, which is the opposite of what this gate is for. Measured 2026-09-08
    on a bundle whose forgery probe was real, replayed 24 of 25 frozen traces and
    scored 0: keys-included reported no carrier at all.
    """
    out = []
    stack = [data]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, (list, tuple)):
            stack.extend(item)
        elif item is not None and not isinstance(item, bool):
            out.append(str(item))
    return out


def gt_slices(gt_text: str, n: int = 12) -> list[str]:
    """Distinctive runs of ground truth, long enough not to occur by chance.

    Single long tokens are the usual shape - a hash, a packed token stream, a base64
    blob. A ground truth made of short rows ("1 cn 5") has none of them, and reading only
    single tokens made this report FAIL a task whose answer-key probe was real and did
    score 0. That was the checker being blind rather than the task being unproven, so
    when nothing single is long enough, consecutive tokens are joined until they are: a
    run of ground-truth rows in order is just as specific as one long token, and a cheat
    still has to carry the answers verbatim to match it. Measured 2026-09-02: adding the
    fallback keeps tasks with real answer-key carriers reporting them and leaves tasks
    without such evidence failing.
    """
    data = json.loads(gt_text)
    flat = json.dumps(data, sort_keys=True).replace("{", " ").replace("}", " ").split()
    out = [chunk for chunk in flat if len(chunk) >= 24][:n]
    if out:
        return out
    for i in range(len(flat)):
        run = ""
        for tok in flat[i:i + 8]:
            run = tok if not run else run + " " + tok
            if len(run) >= 24:
                out.append(run)
                break
        if len(out) >= n:
            break
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    task = ROOT / "tasks" / argv[1]
    # A bundle may keep the answers out of the sandbox uid's reach by parking them in
    # tests/seal/ (span-close-step does, because its verifier executes agent code in a
    # process that has /tests on its import path). Look there too rather than reporting
    # a missing ground truth: two tools disagreeing about where a file lives is how this
    # kit produced a confident wrong answer once before.
    gt = task / "tests" / "gt.json"
    if not gt.is_file():
        gt = task / "tests" / "seal" / "gt.json"
    cheats = sorted((task / "cheat").glob("cheat-*.sh"))
    if not gt.is_file():
        print("no tests/gt.json or tests/seal/gt.json under %s" % task)
        return 1
    if not cheats:
        print("no cheats under %s/cheat" % task)
        return 1

    # Two ways of naming the ground truth, tried in that order. The encoded document
    # includes the keys, which are names the author chose, and a bundle whose keys are
    # long enough will match on those - which is what every earlier task here does. A
    # bundle whose long strings are the answers themselves and whose keys are short (or
    # whose cheat is keyed some other way) matches on nothing there, and the answers are
    # what the gate is actually about, so they are tried as well before reporting a
    # failure. Measured 2026-09-08 across all ten bundles in this repo: the answer-side
    # pass finds the carrier in the two that the encoded-document pass misses, and
    # changes nothing for the eight it already found.
    carriers = []
    for marks in (gt_slices(gt.read_text()), answer_slices(gt.read_text())):
        for sh in cheats:
            body = sh.read_text()
            if sh.name not in carriers and any(m in body for m in marks):
                carriers.append(sh.name)
        if carriers:
            break

    print("== %s" % argv[1])
    if not carriers:
        print("   FAIL no cheat is generated from tests/gt.json, so nothing here shows")
        print("        the verifier rejecting a submission that already has the answers.")
        print("        Generate a forgery family in authoring/emit.py: hijack whatever")
        print("        assembles the graded report, return the ground truth from it, and")
        print("        confirm it scores 0. If it scores 1, the verifier is grading a")
        print("        claim rather than evidence for one.")
        return 1
    print("   forgery probes carrying ground truth: %s" % ", ".join(carriers))

    # The quality review blocked shipped authoring tooling on 2026-09-05, so a bundle's
    # cheat_report may legitimately live at authoring/<slug>/ in the repo root instead.
    root = pathlib.Path(__file__).resolve().parent.parent
    reporter = None
    for cand in (root / "authoring" / task.name / "cheat_report.py",
                 task / "authoring" / "cheat_report.py"):
        if cand.is_file():
            reporter = cand
            break
    if reporter is None:
        print("   FAIL no cheat_report.py to grade them with, in the bundle or at")
        print("        authoring/%s/ in the repo root" % task.name)
        return 1
    proc = subprocess.run([sys.executable, str(reporter)], cwd=str(task),
                          capture_output=True, text=True, timeout=3600)
    tail = proc.stdout.strip().splitlines()[-1:] or ["no output"]
    print("   %s" % tail[0].strip())
    if proc.returncode != 0:
        print(proc.stdout[-2000:])
        return 1
    print("   none")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
