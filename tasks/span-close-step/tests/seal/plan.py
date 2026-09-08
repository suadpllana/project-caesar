"""Choose the run scripts for this trial, as root, before any agent code runs.

The scripts go to the worker; the answers do not. Generating the nonce population
here rather than inside the worker is what keeps the sealed model out of the
sandbox: the worker is handed a list of scripts and has nothing to derive an
expected trace from, and the grader regenerates the same population from the same
nonce afterwards and trusts nothing the worker echoed back.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import gen  # noqa: E402


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    logs = pathlib.Path(sys.argv[sys.argv.index("--logs") + 1])
    seed = (logs / "nonce").read_text(encoding="utf-8").strip()
    per = int((logs / "per").read_text(encoding="utf-8").strip())

    scripts = [{"fam": "hand", "name": n, "lines": cases.ops(n)} for n in cases.ORDER]
    for fam, name, lines in gen.programs(seed, per):
        scripts.append({"fam": fam, "name": name, "lines": list(lines)})
    pathlib.Path(out).write_text(json.dumps(scripts), encoding="utf-8", newline="\n")
    print("planned %d scripts" % len(scripts))


if __name__ == "__main__":
    main()
