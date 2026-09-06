"""Audit the actual worker/grader and model decisions described in clipped probe exports.

The exports omit full edit commands and hidden reasoning. These mutations isolate the
reported decisions; they are not reconstructed agent submissions or new model probes.
Host grading exercises Python assertions, not Linux permissions or process isolation.
"""

from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import harness

ROOT = harness.ROOT
TASK = harness.TASK

INHERIT = '''from wire.reg import SING
from wire.scope import ROOT
from wire import pin

def homes(tbl, st, batch, at):
    out = {}
    for i, nm, up in sorted(batch):
        if tbl[nm].life == SING or out.get(up) == ROOT:
            out[i] = ROOT
        elif tbl[nm].tag:
            out[i] = pin.where(st, at, tbl[nm].tag)
        else:
            out[i] = out.get(up, at)
    return out
'''

RECURSIVE_GATE = '''from wire.reg import SING, SCOPED, reach, cycles

def allow(tbl, st, nm, at):
    if cycles(tbl, nm):
        return False
    for child in reach(tbl, nm):
        r = tbl[child]
        if r.tag and not any(st.tag(sc) == r.tag for sc in st.upto(at)):
            return False
        if r.life == SING and any(tbl[d].life == SCOPED for d in reach(tbl, child)):
            return False
    return True
'''

PROBE = r'''
import json, pathlib, sys
sys.path[:0] = [sys.argv[1], sys.argv[2]]
import cases, gen, oracle
from wire import plan, reg

def normalized(rows):
    return [[str(x) for x in row] for row in rows]

def mismatch(rows, ops):
    try:
        got = normalized(plan.run(reg.load(rows), ops))
    except Exception as exc:
        return True, type(exc).__name__
    return got != normalized(oracle.play(rows, ops)), None

fixed = [name for name, rows, ops in cases.FIXED if mismatch(rows, ops)[0]]
visible = {}
for path in sorted((pathlib.Path(sys.argv[1])/'cases').glob('*.txt')):
    rows, ops = [], []
    for line in path.read_text().splitlines():
        p = line.split()
        if not p or p[0].startswith('#'):
            continue
        if p[0] == 'r':
            tail = [(v if v != '.' else '') for v in p[5:]]
            tail += [''] * (3-len(tail))
            rows.append((p[1], ['sing','scoped','trans'].index(p[2]),
                         [] if p[3] == '.' else p[3].split(','),
                         [] if p[4] == '.' else p[4].split(','), *tail))
        else:
            ops.append(tuple(p[1:]))
    wrong, error = mismatch(rows, ops)
    visible[path.name] = {'wrong': wrong, 'error': error,
                          'want': normalized(oracle.play(rows, ops))}
    if not error:
        visible[path.name]['got'] = normalized(plan.run(reg.load(rows), ops))
bad = 0
first = None
for i in range(1200):
    rows, ops = gen.stream('recovery2-%d' % i, i % 2 == 0)
    wrong, error = mismatch(rows, ops)
    if wrong:
        bad += 1
        if first is None:
            first = {'seed': 'recovery2-%d' % i, 'rows': rows, 'ops': ops,
                     'error': error, 'want': normalized(oracle.play(rows, ops))}
            if not error:
                first['got'] = normalized(plan.run(reg.load(rows), ops))
print(json.dumps({'fixed_wrong': fixed, 'generated_wrong': bad, 'first': first,
                  'visible': visible}))
'''

GRADE = r'''
import importlib.util, inspect, json, os, pathlib, sys
sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location('shr_grade', pathlib.Path(sys.argv[1])/'test_outputs.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.PRISTINE = pathlib.Path(sys.argv[1])/'pristine'
mod.OUT = sys.argv[2]
mod.GT = str(pathlib.Path(sys.argv[1])/'gt.json')
values = {'report': mod.report.__wrapped__(), 'truth': mod.truth.__wrapped__()}
checks = {}
for name, fn in vars(mod).items():
    if name.startswith('test_') and callable(fn):
        try:
            fn(**{k:values[k] for k in inspect.signature(fn).parameters})
            checks[name] = 'pass'
        except Exception as exc:
            checks[name] = type(exc).__name__ + ': ' + str(exc)
print(json.dumps(checks))
'''


def python(code, args, env=None):
    proc = subprocess.run([sys.executable, '-B', '-c', code, *map(str, args)],
                          env=env, capture_output=True, text=True, timeout=120)
    if proc.returncode:
        raise RuntimeError(proc.stderr[-2500:])
    return json.loads(proc.stdout)


def model(name, edits):
    tree = harness.stage(TASK/'solution' if name != 'nop' else None)
    try:
        for rel, change in edits.items():
            path = tree/'wire'/rel
            path.write_text(change(path.read_text()), encoding='utf-8', newline='\n')
        result = python(PROBE, [tree, TASK/'tests'])
        print('%-26s fixed=%2d/22 generated=%4d/1200' %
              (name, len(result['fixed_wrong']), result['generated_wrong']))
        return result
    finally:
        shutil.rmtree(tree.parent)


def full_host_grade(policy):
    if policy is not None and policy.suffix == '.sh':
        import semantic_cheat_check
        tree = semantic_cheat_check.overlay(policy)
        label = policy.name
    else:
        tree = harness.stage(policy)
        label = 'reference' if policy else 'nop'
    report = tree.parent/'report.json'
    env = dict(os.environ, APPDIR=str(tree), WORKAPP=str(tree), SHR_NONCE='recovery2-worker',
               PYTHONDONTWRITEBYTECODE='1')
    try:
        proc = subprocess.run([sys.executable, '-B', str(TASK/'tests'/'runner.py'), str(report)],
                              env=env, capture_output=True, text=True, timeout=120)
        env['RUNNER_OK'] = str(int(proc.returncode == 0))
        checks = python(GRADE, [TASK/'tests', report], env)
        print('actual Python worker/grader (%s): %s' % (label, json.dumps(checks)))
        return checks
    finally:
        shutil.rmtree(tree.parent)


def main():
    completion = lambda s: s.replace(
        'mine = [i for i in sorted(holds) if holds[i] == sc]',
        'mine = [i for i, _nm, _up in co.made if holds.get(i) == sc]')
    variants = {
        'reference': {},
        'nop': {},
        'completion-order': {'plan.py': completion},
        'inherit-marked-owner': {'own.py': lambda _: INHERIT},
        'recursive-admission': {'gate.py': lambda _: RECURSIVE_GATE},
        'invoke-active-charge': {'hold.py': lambda s: s.replace('bk.get(tok, st.top())', 'st.top()')},
        'bind-holder-owner': {'plan.py': lambda s: s.replace(
            'co.build(nm, st.top())', 'holder = co.build(nm, st.top())').replace(
            't = co.mint(f, st.top())', 't = co.mint(f, holds[holder])').replace(
            'hold.note(bk, t, st.top())', 'hold.note(bk, t, holds[holder])')},
        'reject-dead-token': {'gate.py': lambda s: s.replace(
            'r = tbl[nm]', 'if not st.holds(at):\n        return False\n    r = tbl[nm]')},
        'xhigh-n8-reported-homes': {'own.py': lambda _: INHERIT},
        'xhigh-AtT-reported-core': {'own.py': lambda _: INHERIT,
                                     'plan.py': completion, 'gate.py': lambda _: RECURSIVE_GATE},
    }
    report = {name: model(name, changes) for name, changes in variants.items()}
    report['runtime'] = sys.version
    report['host_reference_grader'] = full_host_grade(TASK/'solution')
    report['host_nop_grader'] = full_host_grade(None)
    scripts = list(sorted((TASK/'cheat').glob('cheat-rule-*.sh')))
    scripts += [TASK/'cheat'/name for name in (
        'cheat-forge-answer-key.sh', 'cheat-probe-patch-seal.sh',
        'cheat-probe-rewrite-frozen.sh')]
    report['host_cheat_graders'] = {p.name: full_host_grade(p) for p in scripts}
    dest = ROOT/'probes'/'scope-hold-release'/'recovery-2'/'audit-results.json'
    dest.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    assert all(v == 'pass' for v in report['host_reference_grader'].values())
    assert any(v != 'pass' for v in report['host_nop_grader'].values())
    assert all(any(v != 'pass' for v in checks.values())
               for checks in report['host_cheat_graders'].values())
    for name, check in {
        'cheat-probe-patch-seal.sh': 'test_the_sealed_modules_were_the_ones_we_shipped',
        'cheat-probe-rewrite-frozen.sh': 'test_the_executed_tree_was_the_one_we_shipped',
    }.items():
        failed = [k for k, v in report['host_cheat_graders'][name].items() if v != 'pass']
        assert failed == [check], (name, failed)
    assert not report['reference']['fixed_wrong'] and not report['reference']['generated_wrong']
    assert not any(v['wrong'] for v in report['reference']['visible'].values())
    assert all(v['wrong'] for v in report['nop']['visible'].values())
    assert all(row['fixed_wrong'] or row['generated_wrong'] for name, row in report.items()
               if name in variants and name not in ('reference', 'reject-dead-token'))


if __name__ == '__main__':
    main()
