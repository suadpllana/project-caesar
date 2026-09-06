"""Prove recovery 2 preserved the executable grading contract and reference."""

import ast
import json
from pathlib import Path
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / 'tasks' / 'scope-hold-release'
OLD = ROOT / 'probes' / 'scope-hold-release' / 'recovery-2' / 'before.zip'
RENAME = {'a-wrapper-is-torn-before-what-it-wraps': 'wrapping-follows-reverse-allocation-order'}


def without_docstring(src):
    tree = ast.parse(src)
    if isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
        tree.body.pop(0)
    return ast.dump(tree, include_attributes=False)


with zipfile.ZipFile(OLD) as z:
    prefix = 'scope-hold-release/'
    old = lambda rel: z.read(prefix + rel)
    cfg = tomllib.loads(old('task.toml').decode())
    now = tomllib.loads((TASK/'task.toml').read_text())
    for key in ('artifacts', 'agent', 'verifier', 'environment'):
        assert cfg[key] == now[key], key
    for info in z.infolist():
        rel = info.filename.removeprefix(prefix)
        if rel.startswith(('solution/', 'environment/app_src/wire/', 'tests/pristine/wire/')):
            assert z.read(info) == (TASK/rel).read_bytes(), rel
    for rel in ('tests/oracle.py', 'tests/gen.py', 'tests/test.sh', 'tests/runner.py',
                'tests/reap.py', 'tests/Dockerfile', 'environment/Dockerfile'):
        assert old(rel) == (TASK/rel).read_bytes(), rel
    previous = json.loads(old('tests/gt.json'))
    previous['fixed'] = {RENAME.get(k, k): v for k, v in previous['fixed'].items()}
    assert previous == json.loads((TASK/'tests/gt.json').read_text())
    cases = old('tests/cases.py').decode()
    for before, after in RENAME.items():
        cases = cases.replace(before, after)
    assert cases == (TASK/'tests/cases.py').read_text()
    assert without_docstring(old('tests/test_outputs.py')) == without_docstring(
        (TASK/'tests/test_outputs.py').read_text())

print('UNCHANGED: all expected records, fixed inputs, generator, oracle, assertions,')
print('reference, policies, artifact boundary, timeouts and isolation code.')
print('Only a misleading fixed-case label and grader documentation were corrected.')
