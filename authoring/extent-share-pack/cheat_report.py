"""For each cheat, say which layer catches it, not only that it scored 0.

A cheat that scores 0 for the wrong reason - because the tree it shipped was broken anyway, or
because it crashed on import - proves nothing about the case it was written for. This runs each
cheat's files over the enumerated programs and over a nonce-shaped population and names the first
program that catches it, so the claim in task.toml is a measurement.

The probes are not decided here. They ship the broken tree, so they fail every case in this report
whatever their payload does; whether the payload reached the reward is decided by the two-image run
in tools/docker_trial.py, where the privilege drop, the locked reward channel and the root-only
seal actually exist.
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "extent-share-pack"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import harness  # noqa: E402

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

GT = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
CUT = re.compile(r"cat > (\S+) <<'PYEOF'\n(.*?)\nPYEOF", re.S)


def files(path):
    out = {}
    for name, body in CUT.findall(path.read_text(encoding="utf-8")):
        out[pathlib.Path(name).name] = body + "\n"
    return out


def stage(got):
    room = pathlib.Path(tempfile.mkdtemp(prefix="cheat-"))
    for name, body in got.items():
        (room / name).write_text(body, encoding="utf-8")
    return room


def one(path):
    """Judge a single cheat. Run in a child: a probe payload may call os._exit on import."""
    nonce = gen.programs("cheatreport", 4, big=0)
    run = harness.runner(stage(files(path)))
    for case in cases.ORDER:
        try:
            got = run(cases.ops(case))
        except Exception as exc:
            return case, "raised %s" % type(exc).__name__
        if got != GT[case]:
            return case, "trace differs"
    for _fam, who, lines in nonce:
        try:
            got = run(lines)
        except Exception as exc:
            return who, "raised %s" % type(exc).__name__
        if got != model.expect(lines):
            return who, "nonce program differs"
    return None, ""


def child(path):
    caught, how = one(path)
    sys.stderr.write("\x00RESULT " + json.dumps([caught, how]) + "\n")
    sys.stderr.flush()
    return 0


def main():
    rows = []
    for path in sorted((TASK / "cheat").glob("cheat-*.sh")):
        name = path.stem.replace("cheat-", "")
        proc = subprocess.run([sys.executable, __file__, "--one", str(path)],
                              capture_output=True, text=True)
        mark = [ln for ln in proc.stderr.splitlines() if ln.startswith("\x00RESULT ")]
        if mark:
            caught, how = json.loads(mark[-1].split(" ", 1)[1])
        else:
            caught, how = None, "child exited %d with no verdict" % proc.returncode
        rows.append((name, caught, how))
    width = max(len(r[0]) for r in rows)
    loose = 0
    for name, caught, how in rows:
        if caught is not None:
            print("%-*s   caught by %-14s %s" % (width, name, caught, how))
            continue
        if name.startswith("probe-"):
            print("%-*s   probe: no program catches it, the container run decides it" % (width, name))
        elif name.startswith("slow-"):
            print("%-*s   exactly right and too slow, the clock decides it" % (width, name))
        else:
            loose += 1
            print("%-*s   NOTHING CATCHES IT: %s" % (width, name, how or "no program differs"))
    probes = sum(1 for r in rows if r[0].startswith("probe-"))
    print("\n%d cheats: %d are probes the container run decides, %d loose"
          % (len(rows), probes, loose))
    return 1 if loose else 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--one":
        sys.exit(child(pathlib.Path(sys.argv[2])))
    sys.exit(main())
