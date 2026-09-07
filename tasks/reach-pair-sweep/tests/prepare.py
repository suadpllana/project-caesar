"""Prepare every untrusted-worker input while still running on the trusted side.

The nonce generator imports the sealed model to keep programs well formed, so generation cannot
share a process or a readable directory with submitted collector code. This script runs as root,
writes only the program texts and a pristine runtime into `/work`, and exits before privileges are
dropped. Expected records stay under `/tests`.
"""
import argparse
import json
import pathlib
import shutil

import cases
import gen

HERE = pathlib.Path(__file__).resolve().parent


def prepare(out, tree, nonce, per):
    programs = [{"fam": "hand", "name": name, "lines": cases.CASES[name]}
                for name in cases.ORDER]
    programs += [{"fam": fam, "name": name, "lines": lines}
                 for fam, name, lines in gen.programs(nonce, per)]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(programs), encoding="utf-8")
    shutil.copytree(HERE / "pristine", tree)
    return len(programs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nonce-file", required=True)
    ap.add_argument("--per-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tree", required=True)
    args = ap.parse_args()

    nonce = pathlib.Path(args.nonce_file).read_text(encoding="utf-8").strip()
    per = int(pathlib.Path(args.per_file).read_text(encoding="utf-8").strip())
    count = prepare(pathlib.Path(args.out), pathlib.Path(args.tree), nonce, per)
    print("prepared %d worker programs" % count)


if __name__ == "__main__":
    main()
