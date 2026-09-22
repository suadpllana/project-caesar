"""Fraction of graded scripts each degenerate strategy matches. Authoring only.

docs/INSTRUCTION-CONTRACT.md: record the fraction of cases a shortcut matches as well as its
score, because all-or-nothing grading hides a strategy that is right 90% of the time. Measured
on the hand scripts and one small nonce draw of the same size as the graded one (the deep
family is left out: the shipped tree cannot finish it at all).
"""
import os
import random
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agree  # noqa: E402
import emit  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

sys.path.insert(0, os.path.join(agree.TASK, "tests"))
import cases  # noqa: E402


def strategy_dir(files):
    d = tempfile.mkdtemp(prefix="pkp-short-")
    for name in emit.PARTS:
        shutil.copy(os.path.join(emit.SHIPPED, name), os.path.join(d, name))
    for name, text in files.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(text)
    return d


def main():
    scripts = [("hand", n, cases.CASES[n]) for n in cases.ORDER]
    for fam, name, text in gen.programs("shortcut-draw", 30):
        if fam != "deep":
            scripts.append((fam, name, text))
    want = {name: model.expect(text) for _, name, text in scripts}
    plans = {"nop (shipped tree)": {}}
    for key, (_c, drop_src, audit_src) in emit.SHORTCUTS.items():
        plans[key] = {"drop.py": drop_src, "audit.py": audit_src}
    for label, files in plans.items():
        app = agree.tree_for(strategy_dir(files))
        hand = small = 0
        for fam, name, text in scripts:
            try:
                got = agree.run_tree(app, text)
            except subprocess.TimeoutExpired:
                got = None
            if got == want[name]:
                if fam == "hand":
                    hand += 1
                else:
                    small += 1
        nh = sum(1 for s in scripts if s[0] == "hand")
        print("%-22s hand %d/%d  small nonce %d/%d" % (label, hand, nh, small, len(scripts) - nh), flush=True)


if __name__ == "__main__":
    main()
