"""Builds the graded program list, as root, before any submitted code runs.

The list is the only thing the sandbox needs from this side, so writing it out here lets
`test.sh` shut `/tests` to the sandbox uid entirely: the sealed model, the frozen answers and
the generator all stay where submitted code cannot read them. The programs themselves are not
secret - the worker has to run them - so handing those over costs nothing.
"""
import argparse
import json
import pathlib

import cases
import gen


def spread(nonce, per):
    out = [{"fam": "hand", "name": name, "lines": cases.ops(name)} for name in cases.ORDER]
    for fam, name, lines in gen.programs(nonce, per):
        out.append({"fam": fam, "name": name, "lines": list(lines)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--nonce", required=True)
    ap.add_argument("--per", type=int, required=True)
    args = ap.parse_args()
    body = json.dumps(spread(args.nonce, args.per))
    pathlib.Path(args.out).write_text(body, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
