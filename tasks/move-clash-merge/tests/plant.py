"""Root builds the scenario list before the run and hands over the text only.

The generated families are stepped through the sealed model to know each side's tree between
rounds, so this cannot run inside the process that executes submitted code. What the run
receives is a list of scenarios; what it should print is never written down here.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cases  # noqa: E402
import gen  # noqa: E402


def plan(nonce, count):
    out = [{"name": name, "fam": "hand", "text": cases.CASES[name]} for name in cases.ORDER]
    out += [{"name": name, "fam": name.split("-")[0], "text": text}
            for name, text in gen.batch(nonce, count)]
    return out


def main(argv):
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "60"))
    body = json.dumps(plan(nonce, count), sort_keys=True, separators=(",", ":"))
    with open(argv[1], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
