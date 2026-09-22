"""Build the graded set. Runs as root, before any submitted code, and never executes it.

Writes two files:
  --out    the root-only record the grader trusts: every journal's family, name, text, the
           hash of that text and the lines the sealed model says it must print;
  --texts  the journals alone, name and text, which is all the worker is handed.

The seed was drawn by test.sh after the agent's container was gone. The generator and the
model live beside this file in a directory the worker's uid cannot enter, so nothing the
worker runs can regenerate the true histories or compute the expected lines.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-file", required=True)
    ap.add_argument("--per", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--texts", required=True)
    args = ap.parse_args()
    with open(args.seed_file, encoding="utf-8") as fh:
        seed = fh.read().strip()

    work = [("hand", name, cases.text(name)) for name in cases.ORDER]
    work += gen.programs(seed, args.per)

    graded = []
    for fam, name, text in work:
        graded.append({"fam": fam, "name": name, "text": text, "sig": sig(text),
                       "want": model.expect(text)})
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(graded, fh)
    with open(args.texts, "w", encoding="utf-8", newline="\n") as fh:
        json.dump([{"name": g["name"], "text": g["text"]} for g in graded], fh)
    print("graded journals: %d" % len(graded))


if __name__ == "__main__":
    main()
