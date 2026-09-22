"""Runs the submitted modules. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, and it never imports it. Root has already
staged the tree it runs in - the verifier's pristine copy with the five submitted files laid over
it, root-owned and read-only - and written the graded scripts. This runs the driver on every
script in a fresh interpreter, exactly as `/app/run_db.py <script>` runs, and writes down what
came out, one record per script, as each finishes, so a run the wall clock cuts short still shows
which scripts it got through. The grader treats this file's output as hostile input. A crash, a
hang, or a silent exit loses records, and a lost record is a failure, never a pass.

The wall clock the verifier puts on this process is the task's execution limit, so a correct
store that cannot get through the set in time is scored exactly like a wrong one. The `deep`
family exists for that: stores of about forty thousand rows whose revision chains run six to
seven thousand deep, where replaying one delete per row for the audit is quadratic.
"""
import hashlib
import json
import os
import pathlib
import resource
import subprocess
import sys
import tempfile

TESTS_DIR = os.environ.get("PKP_TESTS", "/tests")
sys.path.insert(0, TESTS_DIR)

import cases  # noqa: E402

TESTS = pathlib.Path(TESTS_DIR)
WORK = pathlib.Path(os.environ.get("PKP_WORK", "/work"))
CAP = 256 * 1024 * 1024


def sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def capped():
    resource.setrlimit(resource.RLIMIT_FSIZE, (CAP, CAP))


def run(here, room, path):
    out = room / "stdout.txt"
    with open(out, "wb") as f:
        got = subprocess.run([sys.executable, str(here / "run_db.py"), str(path)],
                             stdout=f, stderr=subprocess.PIPE, cwd=str(room),
                             preexec_fn=capped)
    if got.returncode != 0:
        tail = got.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]
        return None, ["exit %d" % got.returncode] + tail
    try:
        text = out.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return None, ["output is not utf-8"]
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines, None


def main():
    here = pathlib.Path(sys.argv[sys.argv.index("--tree") + 1])
    out = sys.argv[sys.argv.index("--out") + 1]
    room = pathlib.Path(tempfile.mkdtemp(dir=str(pathlib.Path(out).parent)))
    hand = room / "hand"
    hand.mkdir()
    work = []
    for name in cases.ORDER:
        path = hand / (name + ".txt")
        path.write_text(cases.CASES[name], encoding="utf-8")
        work.append(("hand", name, path))
    work += [("nonce", p.stem, p) for p in sorted((WORK / "scripts").glob("*.txt"))]
    with open(out, "w", encoding="utf-8") as sink:
        for kind, name, path in work:
            text = path.read_text(encoding="utf-8")
            got, err = run(here, room, path)
            sink.write(json.dumps({"kind": kind, "name": name, "sig": sig(text), "got": got,
                                   "err": err}) + "\n")
            sink.flush()


if __name__ == "__main__":
    main()
