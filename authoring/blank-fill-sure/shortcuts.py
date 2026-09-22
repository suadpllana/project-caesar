"""How much of the graded set each degenerate strategy gets right, not only whether it scores.

All-or-nothing grading turns a strategy that matches 90% of programs into a 0 and hides that the
data barely exercises the rule (docs/INSTRUCTION-CONTRACT.md, Shortcuts). This prints, for each
strategy, the share of hand programs and of generated programs whose whole report it matches.

  nop            the shipped engine: a placeholder matches nothing (SQL null logic)
  empty          every query reports nothing
  replay         the worked example's corrected report, whatever the program
  first-rule     positional: only the first rule of each query counts, evaluated correctly
  textbook       each placeholder a value only it holds, rows free of placeholders reported
  possible       every row some filling returns

Usage: python3 authoring/blank-fill-sure/shortcuts.py [seed] [per]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tasks", "blank-fill-sure")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402
import tree  # noqa: E402

REPLAY = ["ans pair 6", "pair 1 1", "pair 1 2", "pair 2 1", "pair 2 2", "pair 3 3", "pair 4 4"]


def first_rules(lines):
    seen, out = set(), []
    for line in lines:
        if line.startswith("rule "):
            q = line.split()[1]
            if q in seen:
                continue
            seen.add(q)
        out.append(line)
    return out


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "shortcuts"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    with open(os.path.join(TASK, "tests", "seal", "gt.json"), encoding="utf-8") as fh:
        gt = json.load(fh)
    hand = [(n, cases.prog(n), gt[n]) for n in cases.ORDER]
    made = [(n, lines, model.expect(lines)) for _f, n, lines in gen.programs(seed, per)]
    ref = tree.runner(os.path.join(TASK, "solution"))
    shipped = tree.runner(None)
    fresh = tree.runner(os.path.join(HERE, "readings", "fresh-all"))
    possible = tree.runner(os.path.join(HERE, "readings", "possible"))

    def text(lines):
        return "\n".join(lines) + "\n"

    def empty(lines):
        st = [l.split()[1] for l in lines if l.startswith("rule ")]
        return ["ans %s 0" % q for q in dict.fromkeys(st)]

    strategies = [
        ("nop", lambda lines: shipped(text(lines))),
        ("empty", empty),
        ("replay", lambda lines: REPLAY),
        ("first-rule", lambda lines: ref(text(first_rules(lines)))),
        ("textbook", lambda lines: fresh(text(lines))),
        ("possible", lambda lines: possible(text(lines))),
    ]
    for name, fn in strategies:
        h = sum(1 for _n, lines, want in hand if fn(lines) == want)
        g = sum(1 for _n, lines, want in made if fn(lines) == want)
        score = int(h == len(hand) and g == len(made))
        print("%-11s hand %2d/%d (%3.0f%%)  generated %3d/%d (%3.0f%%)  score %d"
              % (name, h, len(hand), 100.0 * h / len(hand), g, len(made), 100.0 * g / len(made),
                 score), flush=True)


if __name__ == "__main__":
    main()
