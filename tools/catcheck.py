#!/usr/bin/env python3
"""Does the declared category describe the shipped work, or only the narrative?

The quality review rejected `alias-settle-report` on 2026-09-04 for exactly this: it
declared ML / Evaluation, its brief was set in an evaluation harness, and its environment
contained no ML machinery whatever. The reviewer's words were "nothing about the work
requires ML knowledge, and the 'evaluation harness' framing is narrative".

The mechanical form of that finding is a divergence, not an absence: the category's
vocabulary is present in the PROSE (the brief and the task.toml explanations) and absent
from the ENVIRONMENT (the tree the agent actually works in, path names included, since this
repo degrades identifiers on purpose and a tokenizer may only announce itself as `tok/`).
A task whose category is carried by its story and not by its code is the one that fails.

Measured over this repo when the check was written:

    task (as declared)                env   prose
    rollout-cache-coherence   ML       49      97   passed the quality review
    checkpoint-resume-drift   ML       45      69   passed
    turn-seam-alignment       ML       23      70   passed
    alias-settle-report       ML        0       9   REJECTED, this criterion

Usage: catcheck.py <slug> | --all      Exit 1 on any finding.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"

# One vocabulary per category. These name the machinery a task of that category has to
# ship, not the words its brief is allowed to use. Keep them wide: the check fires on
# nothing at all, so a thin list costs a false positive and a fat one costs nothing.
VOCAB = {
    "ml": r"model|train|infer|tensor|gradient|logit|token|epoch|neural|embed|vocab|bpe|"
          r"attention|weight|sampl|checkpoint|prompt|rollout|\bnet\b|adapter|decode|beam",
    "software": r"cache|queue|index|thread|lock|segment|compact|pars|alloc|buffer|schedul|"
                r"store|node|graph|merge|commit|tree|hash|sort|edit|script|diff|\bseq\b|"
                r"walk|match|line|guard|frame|stack|heap|row|key|tick|refcount",
    "science": r"react|molecul|species|flux|atom|mass|energy|spectr|genom|sequence|"
               r"protein|solv|equilibr|isotop|lattice",
    "operations": r"ledger|register|share|invoic|claim|complian|holder|board|seat|vote|"
                  r"account|audit|settle|payment|balance|filing",
    "security": r"grant|perm|priv|role|acl|token|auth|policy|capab|principal|scope|"
                r"crypt|cipher|signat|sandbox|escalat",
    "hardware": r"circuit|gate|clock|register|wire|module|signal|verilog|rtl|mesh|solid",
    "media": r"audio|note|chord|tempo|pixel|colour|color|render|frame|layout|font",
}


def blob(root: Path, with_names: bool = True) -> str:
    """Everything under root as one lowered string, path names included."""
    out = []
    if not root.exists():
        return ""
    for f in sorted(root.rglob("*")):
        if not f.is_file() or "__pycache__" in str(f):
            continue
        if with_names:
            out.append(str(f.relative_to(root)))
        try:
            out.append(f.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return "\n".join(out).lower()


def check(slug: str) -> int:
    d = TASKS / slug
    toml = (d / "task.toml").read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'^category\s*=\s*"([^"]+)"', toml, re.M)
    if not m:
        print(f"== {slug}\n   FAIL no category in task.toml")
        return 1
    cat = m.group(1).strip().lower()
    pat = VOCAB.get(cat)
    if pat is None:
        print(f"== {slug}\n   FAIL category {cat!r} is not one of the seven")
        return 1

    env = len(re.findall(pat, blob(d / "environment")))
    prose_text = (d / "instruction.md").read_text(encoding="utf-8", errors="ignore") + toml
    prose = len(re.findall(pat, prose_text.lower()))

    print(f"== {slug}\n   category {cat!r}: environment {env}, prose {prose}")
    if env == 0 and prose > 0:
        print(
            f"   FAIL the environment carries no {cat} machinery, but the prose asserts it "
            f"{prose} times.\n"
            f"        The category is being carried by the narrative. A quality reviewer "
            f"reads what\n"
            f"        the work exercises, not where the story is set - pick the category "
            f"that names\n"
            f"        the skill the graded decisions actually need."
        )
        return 1
    if env == 0:
        print(f"   FAIL nothing in the environment evidences category {cat!r}")
        return 1
    print("   none")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    slugs = (
        sorted(p.name for p in TASKS.iterdir() if p.is_dir())
        if args[0] == "--all"
        else args
    )
    return max(check(s) for s in slugs)


if __name__ == "__main__":
    sys.exit(main())
