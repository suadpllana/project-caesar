import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / HERE.name
ENV = TASK / "environment" / "app_src"
SOL = TASK / "solution"
TESTS = TASK / "tests"
CHEAT = TASK / "cheat"

PATHS = ['OUT = "/work/out.json"', 'GT = "/tests/gt.json"', 'PRISTINE = pathlib.Path("/pristine")']
ARTS = ["own.py", "pin.py", "hold.py", "gate.py", "tear.py", "shut.py", "plan.py"]
IGN = shutil.ignore_patterns("__pycache__", "*.pyc")


def shell():
    for c in ("bash", "/usr/bin/bash", r"C:\Program Files\Git\bin\bash.exe"):
        w = shutil.which(c) if not c.startswith("/") and "\\" not in c else (c if pathlib.Path(c).exists() else None)
        if w:
            return w
    raise SystemExit("no bash on PATH")


def stage(tmp):
    root = pathlib.Path(tmp)
    shutil.copytree(TESTS, root / "tests", ignore=shutil.ignore_patterns("pristine", "__pycache__", "*.pyc"))
    shutil.copytree(TESTS / "pristine", root / "pristine", ignore=IGN)
    (root / "work").mkdir()
    shutil.copytree(root / "pristine", root / "work" / "app")
    return root


def rewrite(root):
    src = (TESTS / "test_outputs.py").read_text()
    for line in PATHS:
        if line not in src:
            raise SystemExit("trial.py is stale: %r is no longer in test_outputs.py" % line)
    src = src.replace(PATHS[0], 'OUT = r"%s"' % (root / "work" / "out.json"))
    src = src.replace(PATHS[1], 'GT = r"%s"' % (root / "tests" / "gt.json"))
    src = src.replace(PATHS[2], 'PRISTINE = pathlib.Path(r"%s")' % (root / "pristine"))
    src = src.replace('sys.path.insert(0, "/tests")', 'sys.path.insert(0, r"%s")' % (root / "tests"))
    dst = root / "tests" / "graded.py"
    dst.write_text(src, newline="\n")
    return dst


def apply(root, kind, name):
    app = root / "work" / "app"
    if kind == "oracle":
        for f in ARTS:
            p = SOL / f
            if p.exists():
                shutil.copy(p, app / "wire" / f)
    elif kind == "variant":
        for f in sorted((HERE / "variants" / name).glob("*.py")):
            shutil.copy(f, app / "wire" / f.name)
    elif kind == "cheat":
        r = subprocess.run([shell(), str(CHEAT / name)], cwd=str(app), capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("cheat %s did not apply: %s" % (name, (r.stderr or r.stdout)[-300:]))


def grade(root, graded):
    app = str(root / "work" / "app")
    env = {"APPDIR": app, "SHR_NONCE": "trialnonce", "WORKAPP": app,
           "PYTHONPATH": str(root / "tests"), "SYSTEMROOT": r"C:\Windows",
           "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.run([sys.executable, str(root / "tests" / "runner.py"), str(root / "work" / "out.json")],
                   env=env, capture_output=True, text=True)
    r = subprocess.run([sys.executable, "-m", "pytest", str(graded), "-q", "--no-header",
                        "-p", "no:cacheprovider"], env=env, capture_output=True, text=True, cwd=str(root))
    return (1 if r.returncode == 0 else 0), (r.stdout or "")[-700:]


def run_one(kind, name):
    tmp = tempfile.mkdtemp()
    try:
        root = stage(tmp)
        graded = rewrite(root)
        apply(root, kind, name)
        return grade(root, graded)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--variants", action="store_true")
    ap.add_argument("--one")
    a = ap.parse_args()
    vdir = HERE / "variants"
    if a.one:
        rows = [("cheat", a.one, 0)]
    elif a.variants:
        rows = [("variant", p.name, 1) for p in sorted(vdir.iterdir())] if vdir.exists() else []
    else:
        rows = [("oracle", "solution", 1), ("nop", "shipped", 0)]
        if a.all:
            if vdir.exists():
                rows += [("variant", p.name, 1) for p in sorted(vdir.iterdir())]
            rows += [("cheat", p.name, 0) for p in sorted(CHEAT.glob("*.sh"))]
    bad = 0
    for kind, name, want in rows:
        got, tail = run_one(kind, name)
        if got != want:
            bad += 1
        print("%-8s %-44s want %d got %d%s" % (kind, name, want, got, "" if got == want else "   <-- UNEXPECTED"))
        if got != want:
            print("    " + tail.strip().replace("\n", "\n    ")[:600])
    print("%d rows, %d unexpected" % (len(rows), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
