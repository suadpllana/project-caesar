"""Reference against the sealed model, on hand cases and generated programs.

The reference runs through the real shipped runtime (`run_prog.py` driving `cyc/keep.py`); the
model reimplements everything separately. Agreement over a large population is the evidence
that the contract, not one implementation, is what is being graded.

Everything is written to a temporary tree outside the bundle: authoring scratch left inside the
task folder gets packaged.

    python authoring/reach-pair-sweep/agree.py [per_family]
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "reach-pair-sweep"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def stage(tmp, collector):
    tree = tmp / "tree"
    shutil.copytree(TASK / "environment" / "app_src", tree)
    for f in sorted(pathlib.Path(collector).glob("*.py")):
        shutil.copy(f, tree / "col" / f.name)
    return tree


def record(tree, tmp, name, lines):
    p = tmp / ("%s.txt" % name)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "run_prog.py", str(p)], cwd=tree,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return ["ERROR %s" % r.stderr.strip().splitlines()[-1:]]
    return r.stdout.splitlines()


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 80
    bad, total = [], 0
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        tree = stage(tmp, TASK / "solution")

        for name in cases.ORDER:
            total += 1
            got = record(tree, tmp, name, cases.CASES[name])
            want = model.expect(cases.ops(name))
            if got != want:
                bad.append((name, got, want))

        for fam, name, lines in gen.programs("agree-seed", per):
            total += 1
            got = record(tree, tmp, name, lines)
            want = model.expect(gen.ops(lines))
            if got != want:
                bad.append((name, got, want))

    print("compared %d programs (%d hand, %d generated)"
          % (total, len(cases.ORDER), total - len(cases.ORDER)))
    if bad:
        print("DISAGREED on %d:" % len(bad))
        for name, got, want in bad[:6]:
            print("  %s\n    reference %s\n    model     %s" % (name, got, want))
        return 1
    print("reference and model agree on every one")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
