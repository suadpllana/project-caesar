"""Score the dumbest strategies, and say what fraction of programs each one matches.

All-or-nothing grading turns a strategy that matches most programs into a 0 and hides how
little the population exercises the rules, so the fraction is the number worth reading here,
not the reward (docs/INSTRUCTION-CONTRACT.md).
"""
import json
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import twin  # noqa: E402

GT = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))


def from_cheat(name):
    text = (lab.TASK / "cheat" / ("cheat-%s.sh" % name)).read_text(encoding="utf-8")
    room = pathlib.Path(tempfile.mkdtemp(prefix="ccl-short-"))
    for part, src in re.findall(r"cat > /app/hb/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF", text, re.S):
        (room / part).write_text(src + "\n", encoding="utf-8", newline="\n")
    return room


def score(label, over):
    tree = lab.tree(over)
    hand = sum(1 for name in cases.ORDER if safe(tree, cases.ops(name)) == GT[name])
    made = [body for _f, _n, body in gen.programs("shortcut", 6) if len(body) < 400]
    gen_ok = sum(1 for body in made if safe(tree, body) == twin.expect(body))
    print("%-26s hand %2d/%d   generated %3d/%d"
          % (label, hand, len(cases.ORDER), gen_ok, len(made)), flush=True)


def safe(tree, body):
    try:
        return lab.run(tree, body)
    except Exception:
        return None


def main():
    score("the shipped tree (nop)", None)
    score("grant everything at once", from_cheat("shortcut-grant-all"))
    score("replay the brief's example", from_cheat("shortcut-replay-example"))
    score("the reference", lab.TASK / "solution")


if __name__ == "__main__":
    main()
