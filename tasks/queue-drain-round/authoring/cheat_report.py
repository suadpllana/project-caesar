"""Apply every cheat to a staged tree and say which enumerated stream catches it.

A cheat that dies on an import error has been rejected by nothing, so the stream that
catches it is printed rather than the bare verdict, and the class each cheat belongs to is
asserted rather than eyeballed. A wrong implementation has to be caught by a stream whose
answer it gets wrong. A probe aimed at the reward channel or the sandbox is built on the
shipped tree, so it is wrong on the streams anyway, and what says its layer works is the
two-image trial rather than this. A cheat nothing catches is either a correct
implementation or a hole in the enumerated set, and the generated column tells you which.

    python3 authoring/cheat_report.py [generated-count]
"""
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import json  # noqa: E402

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402


def apply(script, tree):
    r = subprocess.run(["/bin/bash", str(script)],
                       env={"APP": str(pathlib.Path(tree) / "app"), "PATH": "/usr/bin:/bin",
                            "APPDIR": str(pathlib.Path(tree) / "app")},
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("cheat %s exited %d: %s" % (script.name, r.returncode, r.stderr[:400]))


def score(tree, count, seed="c0ffee5eed"):
    r = subprocess.run([sys.executable, str(HERE / "score_one.py"), str(tree), str(count), seed],
                       capture_output=True, text=True, timeout=1800)
    for ln in r.stdout.splitlines():
        if ln.startswith("QDRSCORE "):
            d = json.loads(ln[9:])
            return d["cases"], d["gen"]
    return ["<the run produced nothing: rc=%d>" % r.returncode], ["<no result>"]


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 100
    cases = list(scen.STREAMS)

    rows = []
    for label, over in (("REFERENCE", TASK / "solution"), ("shipped", None)):
        t = harness.stage(None, over)
        bc, bg = score(t, count)
        rows.append((label, bc, bg))
        shutil.rmtree(t, ignore_errors=True)

    unexpected = 0
    for s in sorted((TASK / "cheat").glob("cheat-*.sh")):
        t = harness.stage(None, None)
        apply(s, t)
        bc, bg = score(t, count)
        rows.append((s.stem.replace("cheat-", ""), bc, bg))
        shutil.rmtree(t, ignore_errors=True)

    print("%-30s %-9s %-11s  %s" % ("", "streams", "generated", "first stream that catches it"))
    for name, bc, bg in rows:
        first = bc[0] if bc else ("-" if bg else "NOTHING CATCHES IT")
        print("%-30s %3d/%-5d %4d/%-6d %s"
              % (name, len(cases) - len(bc), len(cases), count - len(bg), count, first))
        if name in ("REFERENCE", "shipped"):
            if name == "REFERENCE" and (bc or bg):
                print("   ^ the reference does not agree with the model")
                unexpected += 1
        elif name.startswith("attest-"):
            if bc or bg:
                print("   ^ this probe is meant to be right on every answer; the two-image"
                      " trial is what has to reject it")
                unexpected += 1
        elif not bc and not bg:
            print("   ^ nothing catches this at all")
            unexpected += 1
    print("attestation probes are value-correct by design and are rejected in the container,")
    print("not here: run tools/docker_trial2.py <slug> --all for those four.")
    print("%d unexpected" % unexpected)
    return 0 if unexpected == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
