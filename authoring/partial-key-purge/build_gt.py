"""Freeze the hand scripts' answers into tests/seal/gt.json. Authoring only.

Answers come from the sealed model and must agree with the brute force (all but the deep
chain, which brute force cannot finish), the reference and the correct variant. When gt.json
already exists, every answer already frozen in it must come out byte-identical; an answer that
moves is a contract change and stops the build.

    python build_gt.py [--show]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(HERE, "..", "..", "tasks", "partial-key-purge")
sys.path.insert(0, HERE)
import agree  # noqa: E402
import brute  # noqa: E402
import model  # noqa: E402

sys.path.insert(0, os.path.join(TASK, "tests"))
import cases  # noqa: E402

GT = os.path.join(TASK, "tests", "seal", "gt.json")
IMPLS = [os.path.join(TASK, "solution"), os.path.join(HERE, "variants", "chk")]
BRUTE_SKIP = {"chain-1500"}


def main():
    show = "--show" in sys.argv
    old = {}
    if os.path.exists(GT):
        with open(GT, encoding="utf-8") as f:
            old = json.load(f)
    trees = [agree.tree_for(i) for i in IMPLS]
    out = {}
    bad = 0
    for name in cases.ORDER:
        text = cases.CASES[name]
        why = agree.consistent(text) if name not in BRUTE_SKIP else None
        if why:
            bad += 1
            print("INCONSISTENT", name, why)
        want = model.expect(text)
        checks = [("brute", None if name in BRUTE_SKIP else brute.run(text))]
        checks += [(os.path.basename(i), agree.run_tree(t, text)) for i, t in zip(IMPLS, trees)]
        for who, got in checks:
            if got is not None and got != want:
                bad += 1
                print("DISAGREE", name, who)
        if name in old and old[name] != want:
            bad += 1
            print("MOVED", name, "- a frozen answer changed; that is a contract change")
        out[name] = want
        if show and name not in BRUTE_SKIP:
            print("==", name)
            for line in want:
                print("  ", line)
    if bad:
        print(bad, "problems; gt.json not written")
        return 1
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    with open(GT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", len(out), "answers;", len([n for n in out if n in old]), "were frozen already")
    return 0


if __name__ == "__main__":
    sys.exit(main())
