#!/usr/bin/env python3
"""Run every cheat and say which enumerated case catches it - not only that it scored 0.

A cheat that scores 0 tells you nothing about why. The wrong-reading cheats each name a
graded decision, so each must die on the enumerated segment file written for that decision;
if one only dies on the generated population, the hand set does not pin that rule and a
failure would read as bad luck rather than as a named rule.

Three kinds are not run here and say so:

  probe-*            they write /logs/verifier, fork, or exit the interpreter. They are
                     isolation probes and only the two-container trial means anything for
                     them (tools/docker_trial.py scan-chunk-pick --all).
  slow-rowid-set     exactly correct and too slow: nothing it prints is wrong, so no case
                     can catch it and only the wall clock does.
  forge-hand         carries the frozen answers, so it is supposed to reproduce every
                     enumerated file and to fail on the population it could not have seen.
                     Both halves are asserted here.

Which case fires first is the order of `cases.ORDER`, not the case named for the reading;
that the named case separates the reading is what `tools/readingcheck.py` measures.

Exit 1 when any other cheat has no enumerated case behind it.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "scan-chunk-pick"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import host  # noqa: E402
import model  # noqa: E402

BODY = re.compile(r"cat > (\S+) <<'PYEOF'\n(.*?)\nPYEOF", re.S)
TIME_ONLY = {"cheat-slow-rowid-set.sh"}
FORGERY = {"cheat-forge-hand.sh"}


def files_of(sh):
    return {m.group(1): m.group(2) for m in BODY.finditer(sh.read_text(encoding="utf-8"))}


def run_generated(policy, per):
    """The first generated segment file the cheat gets wrong, if any."""
    script = """
import json, sys
sys.path.insert(0, %r)
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import gen, model, host
eng = host.engine(host.tree(%r))
for fam, name, lines in gen.programs("cheat-report", %d):
    if fam in ("wide", "deep"):
        continue
    try:
        got = eng.run("\\n".join(lines) + "\\n")
    except Exception as exc:
        print(json.dumps([name, "raised " + type(exc).__name__])); break
    if got != model.expect(lines):
        print(json.dumps([name, "trace differs"])); break
else:
    print(json.dumps([None, "no generated file catches it"]))
""" % (str(HERE), str(TASK / "tests"), str(TASK / "tests" / "seal"), str(policy), per)
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                          timeout=900)
    import json
    if proc.returncode != 0:
        return None, "could not be run"
    return tuple(json.loads(proc.stdout.strip().splitlines()[-1]))


def run_isolated(policy, names):
    """Import the cheat in a child process, so a cheat that leaks module state cannot
    contaminate the next one, and report the first enumerated case it gets wrong."""
    script = """
import json, sys
sys.path.insert(0, %r)
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import cases, model, host
eng = host.engine(host.tree(%r))
for name in %r:
    lines = cases.prog(name)
    try:
        got = eng.run("\\n".join(lines) + "\\n")
    except Exception as exc:
        print(json.dumps([name, "raised " + type(exc).__name__])); break
    if got != model.expect(lines):
        print(json.dumps([name, "trace differs"])); break
else:
    print(json.dumps([None, "no enumerated case catches it"]))
""" % (str(HERE), str(TASK / "tests"), str(TASK / "tests" / "seal"), str(policy), names)
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                          timeout=900)
    if proc.returncode != 0:
        return None, "the cheat could not be run: %s" % proc.stderr.strip().splitlines()[-1:]
    import json
    return tuple(json.loads(proc.stdout.strip().splitlines()[-1]))


def main():
    order = list(cases.ORDER)
    bad = []
    lines_out = []
    for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
        if sh.name.startswith("cheat-probe-"):
            lines_out.append("%-34s container only (isolation probe)" % sh.name)
            continue
        room = pathlib.Path(tempfile.mkdtemp(prefix="cr-"))
        try:
            for p in (TASK / "solution").glob("*.py"):
                shutil.copyfile(p, room / p.name)
            for path, src in files_of(sh).items():
                name = path.rsplit("/", 1)[-1]
                (room / name).write_text(src + "\n", encoding="utf-8")
            case, why = run_isolated(room, order)
            if sh.name in FORGERY:
                gen_case, gen_why = run_generated(room, 3)
                if case is not None:
                    bad.append((sh.name, "the answer key does not even reproduce %s" % case))
                elif gen_case is None:
                    bad.append((sh.name, "nothing outside the enumerated set catches it"))
                else:
                    lines_out.append("%-34s reproduces all %d enumerated files; "
                                     "caught by %s (%s)"
                                     % (sh.name, len(order), gen_case, gen_why))
                continue
            if sh.name in TIME_ONLY:
                if case is None:
                    lines_out.append("%-34s correct on every enumerated case; "
                                     "the wall clock is what rejects it" % sh.name)
                else:
                    bad.append((sh.name, "expected to be exactly correct, but %s %s"
                                % (case, why)))
                continue
            if case is None:
                bad.append((sh.name, why))
            else:
                lines_out.append("%-34s caught by %s (%s)" % (sh.name, case, why))
        finally:
            shutil.rmtree(room, ignore_errors=True)

    for line in lines_out:
        print("   " + line)
    for name, why in bad:
        print("   NOT CAUGHT  %s: %s" % (name, why))
    print("%d cheats, %d without an enumerated case behind them" % (
        len(list((TASK / "cheat").glob("cheat-*.sh"))), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
