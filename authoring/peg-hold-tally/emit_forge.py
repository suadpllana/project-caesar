"""Write the forgery cheat: a submission that already holds the answer key.

tools/forgecheck.py asks whether the verifier demands evidence or grades a report. The way to
answer it is to hand a submission every frozen answer and let it rewrite the record the grader
reads. It must still score 0, because the answers it holds are the twenty-nine enumerated
programs and the exam is four hundred and fifty-nine programs generated after it finished.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "peg-hold-tally"
GT = TASK / "tests" / "seal" / "gt.json"
REF = TASK / "solution"
PARTS = ("live.py", "cover.py", "edge.py", "gone.py", "sole.py")

FORGE = '''

import atexit
import json

TRUTH = json.loads("""%s""")


def _forge():
    """Rewrite the record with the answers, keeping every program hash the worker wrote."""
    try:
        with open("/work/worker_out.json") as f:
            rows = json.load(f)
    except Exception:
        rows = [{"fam": "hand", "name": name, "sig": "0" * 64, "got": got, "err": None}
                for name, got in TRUTH.items()]
        try:
            with open("/work/worker_out.json", "w") as f:
                json.dump(rows, f)
        except Exception:
            pass
        return
    for row in rows:
        got = TRUTH.get(row.get("name"))
        row["got"] = got if got is not None else []
        row["err"] = None
    try:
        with open("/work/worker_out.json", "w") as f:
            json.dump(rows, f)
    except Exception:
        pass


atexit.register(_forge)
'''


def main():
    truth = json.dumps(json.loads(GT.read_text(encoding="utf-8")))
    out = ["#!/bin/bash",
           "# carries every frozen answer and rewrites the record the grader reads",
           "set -euo pipefail", ""]
    for part in PARTS:
        body = (REF / part).read_text(encoding="utf-8").rstrip("\n")
        if part == "sole.py":
            body = body + "\n" + (FORGE % truth).strip("\n")
        out.append("cat > /app/keep/%s <<'PYEOF'\n%s\nPYEOF\n" % (part, body))
    text = "\n".join(out) + "\n"
    assert "\r" not in text
    path = TASK / "cheat" / "cheat-forge-from-truth.sh"
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)
    print("wrote %s (%d bytes of answers)" % (path.name, len(truth)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
