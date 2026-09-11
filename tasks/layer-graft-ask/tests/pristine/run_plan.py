import sys

from cfg import ans, lex, past


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_plan.py <plan>\n")
        return 2
    with open(argv[1], "r", encoding="utf-8") as fh:
        text = fh.read()
    try:
        plan = lex.parse(text)
    except ValueError as exc:
        sys.stderr.write("bad plan: %s\n" % exc)
        return 2
    hist = past.build(plan)
    out = []
    for q in plan.asks:
        out.append(ans.answer(hist, q))
    sys.stdout.write("".join(line + "\n" for line in out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
