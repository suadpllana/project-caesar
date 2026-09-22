"""Build the graded segment files, before the clock on the submitted engine starts.

Generating the population is the verifier's work, not the engine's, so it happens here, as
root, and the result is handed to the worker as a root-owned file. The wall clock the worker
runs under is then the engine's own time and nothing else, which is what the brief states.
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, "/tests")

import cases  # noqa: E402
import gen  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nonce", required=True)
    ap.add_argument("--per", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    seed = pathlib.Path(args.nonce).read_text(encoding="utf-8").strip()
    work = [{"fam": "hand", "name": name, "lines": cases.prog(name)} for name in cases.ORDER]
    work += [{"fam": fam, "name": name, "lines": lines}
             for fam, name, lines in gen.programs(seed, args.per)]
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(work, fh)
    print("prepared %d segment files" % len(work))


if __name__ == "__main__":
    main()
