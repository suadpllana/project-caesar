import json
import sys

from kern.lex import parse
from kern.loop import Loop


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("run_prog.py <file> [entry]\n")
        return 2
    root = argv[2] if len(argv) > 2 else "main"
    with open(argv[1]) as fh:
        progs = parse(fh.read())
    rows = []
    lp = Loop(progs, rows.append)
    lp.run(root)
    out = {
        "trace": [list(r) for r in rows],
        "toks": [[f.fid, f.pid, list(f.toks)] for f in lp.fs],
    }
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
