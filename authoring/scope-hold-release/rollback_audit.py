"""Recovery 3: regression contract, literal traces, variants and real host grader."""

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time
import zipfile

import harness
import recovery_audit
import semantic_cheat_check

TASK = harness.TASK
DEST = harness.ROOT / "probes/scope-hold-release/recovery-3"
sys.path.insert(0, str(TASK / "tests"))
import cases
import gen
import oracle


LITERALS = {
    "a-failed-construction-rolls-back-what-it-finished":
        ["refused job 1", "torn deep 1 job", "torn warm 1 job"],
    "a-failed-singleton-still-roots-its-rollback":
        ["refused app 1", "torn pool 0 app"],
    "rollback-does-not-remove-an-older-cache-entry":
        ["refused job 1", "torn fresh 1 job", "torn warm 1 warm"],
    "rollback-clears-a-new-cache-entry":
        ["refused job 1", "torn seat 1 job", "torn seat 1 seat"],
    "wrapped-and-marked-rollback-keeps-all-three-orders":
        ["refused job 2", "torn crumb 2 job", "torn tail 2 job",
         "torn leaf 2 job", "torn skin 1 job"],
    "a-cache-hit-skips-an-unavailable-constructor":
        ["refused hub 2", "torn hub 1 hub", "torn seat 1 seat"],
    "factory-failure-uses-capture-home-and-invocation-refusal":
        ["refused mk 2", "torn note 1 mk", "torn bad 1 mk", "torn note 1 mk",
         "torn mk 1 mk", "torn hub 1 hub"],
    "admission-still-precedes-any-constructor-failure": ["refused app 1"],
}


def norm(records):
    return [[str(x) for x in row] for row in records]


def contract():
    archive = harness.ROOT / "probes/scope-hold-release/recovery-2/quality-rejected.zip"
    with zipfile.ZipFile(archive) as z:
        old = json.loads(z.read("scope-hold-release/tests/gt.json"))["fixed"]
        assert len(old) == 22
        for name, rows, ops in cases.FIXED[:22]:
            assert norm(oracle.play(rows, ops)) == old[name], name
        for rel in ("tests/test.sh", "tests/reap.py", "tests/Dockerfile",
                    "environment/Dockerfile"):
            assert z.read("scope-hold-release/" + rel) == (TASK / rel).read_bytes(), rel
    for name, rows, ops in cases.FIXED:
        if name in LITERALS:
            got = [" ".join(map(str, row)) for row in oracle.play(rows, ops)]
            assert got == LITERALS[name], (name, got, LITERALS[name])
    assert len(cases.FIXED) == 42
    for src in (TASK / "environment/app_src").rglob("*"):
        if src.is_file() and "__pycache__" not in src.parts:
            rel = src.relative_to(TASK / "environment/app_src")
            assert src.read_bytes() == (TASK / "tests/pristine" / rel).read_bytes(), rel
    return "22 legacy outputs and isolation unchanged; 8 literal traces agree; pristine matches"


def visible(policy):
    tree = harness.stage(policy)
    try:
        code = r"""
import json, pathlib, runpy, sys
tree, tests = map(pathlib.Path, sys.argv[1:3])
sys.path[:0] = [str(tree), str(tests)]
import oracle
from wire import plan
sys.argv = ['run_wire.py', str(tree/'cases/plain.txt')]
from contextlib import redirect_stdout
import io
with redirect_stdout(io.StringIO()):
    api = runpy.run_path(str(tree/'run_wire.py'))
out = {}
for path in sorted((tree/'cases').glob('*.txt')):
    tbl, ops = api['parse'](path)
    rows = [(n,r.life,r.deps,r.facs,r.tag,r.wraps,r.shut,r.fail) for n,r in tbl.items()]
    got = plan.run(tbl, ops)
    out[path.name] = got == oracle.play(rows, ops)
print(json.dumps(out))
"""
        return recovery_audit.python(code, [tree, TASK / "tests"])
    finally:
        shutil.rmtree(tree.parent)


def main():
    started = time.perf_counter()
    results = {"runtime": sys.version, "contract": contract()}
    print(results["contract"])
    variants = [("reference", harness.REF)]
    variants += [(p.name, p) for p in sorted((Path(__file__).parent / "variants").glob("ok-*"))]
    results["variants"] = {}
    for name, policy in variants:
        check = harness.check(policy, 1200)
        assert not check["fixed"] and not check["generated"], (name, check)
        results["variants"][name] = check
        print(name, "agrees on 42 fixed + 2400 generated")
    results["visible_reference"] = visible(harness.REF)
    results["visible_nop"] = visible(None)
    assert all(results["visible_reference"].values())
    assert not any(results["visible_nop"].values())
    results["host_grader"] = {}
    targets = [("reference", harness.REF), ("nop", None)]
    targets += [(p.name, p) for p in sorted((TASK / "cheat").glob("cheat-rule-*.sh"))]
    targets += [(name, TASK / "cheat" / name) for name in (
        "cheat-forge-answer-key.sh", "cheat-probe-patch-seal.sh",
        "cheat-probe-rewrite-frozen.sh")]
    for name, policy in targets:
        with contextlib.redirect_stdout(io.StringIO()):
            result = recovery_audit.full_host_grade(policy)
        passed = all(v == "pass" for v in result.values())
        assert passed == (name == "reference"), (name, result)
        results["host_grader"][name] = result
        print(name, "PASS" if passed else "rejected")
    for name, check in {
        "cheat-probe-patch-seal.sh": "test_the_sealed_modules_were_the_ones_we_shipped",
        "cheat-probe-rewrite-frozen.sh": "test_the_executed_tree_was_the_one_we_shipped",
    }.items():
        failed = [k for k, v in results["host_grader"][name].items() if v != "pass"]
        assert failed == [check], (name, failed)
    results["mutants"] = {}
    for script in sorted((TASK / "cheat").glob("cheat-rule-*.sh")):
        tree = semantic_cheat_check.overlay(script)
        try:
            check = semantic_cheat_check.replay(tree, 300)
        finally:
            shutil.rmtree(tree.parent)
        assert check["fixed"] or check["generated"], script.name
        results["mutants"][script.name] = check
    results["elapsed_sec"] = round(time.perf_counter() - started, 3)
    results["limits"] = "Host Python only; Docker/Harbor/isolation and external model gates unrun"
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "validation.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print("ALL HOST CHECKS PASSED", results["elapsed_sec"], "seconds")


if __name__ == "__main__":
    main()
