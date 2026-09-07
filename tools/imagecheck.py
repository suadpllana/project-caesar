"""Would the environment image actually build, and does the runtime work inside it?

A reference-verification rejection on 2026-09-07: the environment tree was rebuilt and the
Dockerfile kept copying directory names that no longer existed. `COPY` on a missing source fails
the build, so oracle and nop both died in about five seconds with a compose error and no test
ever ran. Every local gate was green, because none of them looked at the Dockerfile's COPY lines
and the host emulation copies `app_src` straight out of the working tree.

This closes that gap without Docker. It interprets the COPY and WORKDIR instructions of
`environment/Dockerfile` against the build context, honouring `.dockerignore`, and assembles the
tree the image would actually contain. Then it drops the reference solution in and runs the
programs the bundle ships, so a file the image is missing shows up as an ImportError here rather
than as a compose failure on the platform.

It is an interpretation, not Docker: it does not run `RUN` lines, install packages, or check the
base image. What it does check is the part that broke.

Usage: python tools/imagecheck.py <slug>      Exit 1 on any finding.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def ignored(rel, patterns):
    text = rel.as_posix()
    for pat in patterns:
        p = pat.strip()
        if not p or p.startswith("#"):
            continue
        p = p.lstrip("/")
        if p.startswith("**/"):
            p = p[3:]
            if any(part == p or pathlib.PurePosixPath(part).match(p) for part in rel.parts):
                return True
        if pathlib.PurePosixPath(text).match(p) or text.startswith(p.rstrip("/") + "/"):
            return True
        if any(pathlib.PurePosixPath(part).match(p) for part in rel.parts):
            return True
    return False


def build_tree(ctx, dockerfile, out):
    """Apply WORKDIR and COPY to assemble what the image would hold under the workdir."""
    dockerignore = ctx / ".dockerignore"
    patterns = dockerignore.read_text(encoding="utf-8").splitlines() if dockerignore.is_file() else []

    workdir = "/"
    copied = 0
    problems = []
    for line in dockerfile.read_text(encoding="utf-8").splitlines():
        stripped = line.split("#", 1)[0].strip()
        w = re.match(r"WORKDIR\s+(\S+)", stripped, re.IGNORECASE)
        if w:
            workdir = w.group(1)
            continue
        m = re.match(r"COPY\s+(?:--[^\s]+\s+)*(.+)$", stripped, re.IGNORECASE)
        if not m:
            continue
        parts = m.group(1).split()
        if len(parts) < 2:
            continue
        srcs, dest = parts[:-1], parts[-1]
        if not dest.startswith("/"):
            dest = workdir.rstrip("/") + "/" + dest
        for src in srcs:
            s = ctx / src.rstrip("/")
            if not s.exists():
                problems.append("COPY source %r does not exist in the build context" % src)
                continue
            if s.is_dir():
                for f in sorted(s.rglob("*")):
                    if not f.is_file():
                        continue
                    rel = f.relative_to(ctx)
                    if ignored(rel, patterns):
                        continue
                    inner = f.relative_to(s)
                    target = out / dest.lstrip("/") / inner
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(f, target)
                    copied += 1
            else:
                rel = s.relative_to(ctx)
                if ignored(rel, patterns):
                    continue
                target = out / dest.lstrip("/")
                if dest.endswith("/"):
                    target = out / dest.lstrip("/") / s.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(s, target)
                copied += 1
    return workdir, copied, problems


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1])
        return 2
    task = ROOT / "tasks" / argv[1]
    ctx = task / "environment"
    dockerfile = ctx / "Dockerfile"
    if not dockerfile.is_file():
        print("no environment/Dockerfile under %s" % task)
        return 1

    print("== %s" % argv[1])
    findings = []
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td)
        workdir, copied, problems = build_tree(ctx, dockerfile, out)
        findings.extend(problems)
        print("   image would hold %d files, workdir %s" % (copied, workdir))
        if copied == 0:
            findings.append("the image would be empty - nothing was copied in")

        app = out / workdir.lstrip("/")
        soln = task / "solution"
        if not problems and app.is_dir() and soln.is_dir():
            # the reference lands wherever solve.sh puts it; find it by matching basenames
            placed = 0
            for f in sorted(soln.glob("*.py")):
                for dest in app.rglob(f.name):
                    shutil.copy(f, dest)
                    placed += 1
                    break
            runner = next((p for p in sorted(app.glob("run_*.py"))), None)
            progs = sorted(p for p in app.rglob("*.txt") if p.is_file())[:6]
            if runner is None or not progs:
                # Layout differs from bundle to bundle; the COPY audit above is the part that
                # generalises, so a runner this cannot identify is skipped, never failed.
                print("   no runner or case files identified - COPY audit only")
            else:
                print("   reference placed into %d file(s); running %d shipped program(s)"
                      % (placed, len(progs)))
                for prog in progs:
                    r = subprocess.run([sys.executable, runner.name, str(prog)], cwd=app,
                                       capture_output=True, text=True, timeout=300)
                    if r.returncode != 0:
                        last = r.stderr.strip().splitlines()[-1:] or ["(no stderr)"]
                        findings.append("%s failed inside the image: %s" % (prog.name, last[0]))
                    elif not r.stdout.strip():
                        print("      %-14s ran, printed nothing" % prog.name)
                    else:
                        print("      %-14s %d line(s)" % (prog.name, len(r.stdout.splitlines())))

    print()
    if findings:
        for f in findings:
            print("   FAIL %s" % f)
        return 1
    print("   none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
