"""Writes the graded nonce scripts and their answers. Root only, before the worker starts.

The scripts go where the worker can read them and nothing more; the answers go into this
sealed directory, which is chmod 700 before any agent code runs. Generation tracks the store
through the model so that every delete names rows that are present when it runs.
"""
import argparse
import hashlib
import json
import os

import gen
import model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-file", required=True)
    ap.add_argument("--per", type=int, required=True)
    ap.add_argument("--scripts", required=True)
    ap.add_argument("--answers", required=True)
    args = ap.parse_args()
    with open(args.seed_file, encoding="utf-8") as f:
        seed = f.read().strip()
    answers = {}
    for fam, name, text in gen.programs(seed, args.per):
        path = os.path.join(args.scripts, name + ".txt")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.chmod(path, 0o644)
        answers[name] = {"fam": fam, "sig": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                         "want": model.expect(text)}
    with open(args.answers, "w", encoding="utf-8") as f:
        json.dump(answers, f)
    os.chmod(args.answers, 0o600)
    print("wrote %d scripts" % len(answers))


if __name__ == "__main__":
    main()
