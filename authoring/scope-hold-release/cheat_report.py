import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trial  # noqa: E402

RULE = "test_the_named_cases_match_the_rules"
GEN = "test_the_generated_streams_match_the_rules"
SEAL = "test_the_sealed_modules_were_the_ones_we_shipped"
TREE = "test_the_executed_tree_was_the_one_we_shipped"
ALIVE = "test_the_run_produced_a_report"

EXPECT = {
    "cheat-probe-rewrite-frozen.sh": {TREE},
    "cheat-probe-patch-seal.sh": {SEAL},
}


def failures(kind, name):
    tmp = tempfile.mkdtemp()
    try:
        root = trial.stage(tmp)
        graded = trial.rewrite(root)
        trial.apply(root, kind, name)
        app = str(root / "work" / "app")
        env = {"APPDIR": app, "SHR_NONCE": "trialnonce", "WORKAPP": app,
               "PYTHONPATH": str(root / "tests"), "SYSTEMROOT": r"C:\Windows",
               "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
        subprocess.run([sys.executable, str(root / "tests" / "runner.py"),
                        str(root / "work" / "out.json")], env=env, capture_output=True, text=True)
        r = subprocess.run([sys.executable, "-m", "pytest", str(graded), "-q", "--no-header",
                            "-rf", "-p", "no:cacheprovider"], env=env, capture_output=True,
                           text=True, cwd=str(root))
        got = set(re.findall(r"FAILED .*?::(\w+)", r.stdout))
        return got, r.returncode
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    bad = 0
    for sh in sorted(trial.CHEAT.glob("*.sh")):
        got, rc = failures("cheat", sh.name)
        if rc == 0:
            print("%-46s SCORED 1" % sh.name)
            bad += 1
            continue
        if not got:
            print("%-46s rejected but no assertion named it" % sh.name)
            bad += 1
            continue
        want = EXPECT.get(sh.name)
        note = ""
        if want is not None:
            if got != want:
                note = "   <-- expected exactly %s" % ", ".join(sorted(want))
                bad += 1
        elif got <= {ALIVE}:
            note = "   <-- caught only by liveness"
            bad += 1
        print("%-46s %s%s" % (sh.name, ",".join(sorted(got)), note))
    print("%d cheats, %d unexpected" % (len(list(trial.CHEAT.glob('*.sh'))), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
