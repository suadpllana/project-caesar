"""A host emulation of the trial: real registers, real records, real comparison, no container.

It is here for speed while authoring. It does NOT cover the privilege drop, the root-owned
reward channel, the unreadable answers, the inherited descriptor or the process teardown,
so a clean run here says the determination is right and says nothing about the isolation.
tools/docker_trial2.py <slug> --all is the run that covers those.

Usage:
    python3 authoring/trial.py                 the reference
    python3 authoring/trial.py --all           the reference, the shipped tree, every cheat
    python3 authoring/trial.py --dir PATH      one policy directory
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402

BLOCK = re.compile(r"cat > /app/pol/(\S+) <<'SRSEOF'\n(.*?)\nSRSEOF", re.S)
ROUNDS = 320

# Two probes are the reference with every answer correct and one attestation interfered
# with. Nothing here implements those attestations, so they score 1 here and 0 in the
# container. Reporting them as failures would teach the next session to ignore this
# script; reporting them as passes would be a lie. They are called out instead.
ATTEST = ("cheat-patch-elect.sh", "cheat-kill-monitor.sh")


def policy_of(sh):
    d = Path(tempfile.mkdtemp(prefix="trial-"))
    for m in BLOCK.finditer(sh.read_text(encoding="utf-8")):
        (d / m.group(1)).write_text(m.group(2) + "\n", encoding="utf-8", newline="\n")
    return d


def grade(policy, texts, want):
    try:
        got = harness.drive_text(harness.stage(policy), texts)
    except RuntimeError as exc:
        return 0, str(exc).splitlines()[-1][:60]
    off = [i for i, (a, b) in enumerate(zip(got, want)) if a != b]
    return (0 if off else 1), ("%d of %d registers wrong" % (len(off), len(texts)) if off
                               else "every register")


def main(argv):
    texts = [t for _, t in cases.CASES] + [t for _, t in gen.batch("trial", ROUNDS)]
    want = [oracle.determine(t) for t in texts]

    if "--dir" in argv:
        d = Path(argv[argv.index("--dir") + 1])
        if not d.is_absolute():
            d = TASK / d
        score, why = grade(d, texts, want)
        print("%-40s reward=%d  %s" % (d.name, score, why))
        return 0 if score == 1 else 1

    rows = [("oracle", harness.REF, 1), ("nop", None, 0)]
    if "--all" in argv:
        rows += [(sh.name, policy_of(sh), 0)
                 for sh in sorted((TASK / "cheat").glob("cheat-*.sh"))]
    ok = 0
    held = []
    for name, policy, expect in rows:
        score, why = grade(policy, texts, want)
        if name in ATTEST:
            held.append(name)
            print("%-40s reward=%d  not covered here: every answer is correct and the "
                  "layer it attacks lives in the container" % (name, score))
            continue
        good = score == expect
        ok += good
        print("%-40s reward=%d expected=%d %-4s %s"
              % (name, score, expect, "PASS" if good else "FAIL", why))
    total = len(rows) - len(held)
    print("\n%d/%d behaved as required" % (ok, total))
    if held:
        print("%d probe(s) not covered by this emulation: %s" % (len(held), ", ".join(held)))
        print("Run tools/docker_trial2.py share-register-screen --all for those.")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
