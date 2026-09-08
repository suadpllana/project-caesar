"""Whole-solver readings of the brief, and how much of the graded surface each moves.

Every entry here is a complete, runnable policy: the reference with exactly one
decision read the other way. That is the point - an ablation of a module nobody
would write measures nothing, so each of these is a plan an agent could actually
hand in. A reading that moves no program is a decision the verifier does not
grade, and either the population or the contract has to change.
"""
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "packed-doc-settlement"))
sys.path.insert(0, str(ROOT / "tasks" / "packed-doc-settlement" / "tests" / "seal"))

import harness  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

REF = ROOT / "tasks" / "packed-doc-settlement" / "solution"
ENV = ROOT / "tasks" / "packed-doc-settlement" / "environment" / "app_src" / "train"

STALE_PICK = '''import math

from train import feat


def take(run, mb):
    acc = run.st.setdefault("acc", {})
    cnt = run.st.setdefault("cnt", {})
    for sq in mb:
        for key, i in sq:
            name, n, t = run.feed.info(key)
            x = feat.vec(name, i)
            s = sum(run.w[k] * x[k] for k in range(4))
            a = acc.get(key)
            if a is None:
                a = [s, 0.0, [0.0, 0.0, 0.0, 0.0], 0.0, [0.0, 0.0, 0.0, 0.0]]
                acc[key] = a
            if s > a[0]:
                f = math.exp(a[0] - s)
                a[1] *= f
                a[2] = [v * f for v in a[2]]
                a[0] = s
            e = math.exp(s - a[0])
            a[1] += e
            for k in range(4):
                a[2][k] += e * x[k]
            if i == t:
                a[3] = s
                a[4] = x
            cnt[key] = cnt.get(key, 0) + 1


def close(run):
    cnt = run.st.get("cnt", {})
    seen = run.st.setdefault("seen", {})
    done = []
    for key, c in cnt.items():
        seen[key] = seen.get(key, 0) + c
        _, n, t = run.feed.info(key)
        if seen[key] >= n:
            del seen[key]
            if t >= 0:
                done.append(key)
    run.st["cnt"] = {}
    return sorted(done)
'''

STALE_FOLD = '''import math


def one(run, key):
    a = run.st["acc"].pop(key)
    loss = a[0] + math.log(a[1]) - a[3]
    grad = [a[2][k] / a[1] - a[4][k] for k in range(4)]
    return loss, grad
'''

MB_ORDER_PICK = '''def take(run, mb):
    cnt = run.st.setdefault("cnt", {})
    order = run.st.setdefault("order", [])
    for sq in mb:
        for key, i in sq:
            cnt[key] = cnt.get(key, 0) + 1
            if key not in order:
                order.append(key)


def close(run):
    cnt = run.st.get("cnt", {})
    seen = run.st.setdefault("seen", {})
    done = []
    for key in run.st.get("order", []):
        c = cnt.get(key, 0)
        if not c:
            continue
        seen[key] = seen.get(key, 0) + c
        _, n, t = run.feed.info(key)
        if seen[key] >= n:
            del seen[key]
            if t >= 0:
                done.append(key)
    run.st["cnt"] = {}
    run.st["order"] = []
    return done
'''

MASK_PICK = '''def take(run, mb):
    cnt = run.st.setdefault("cnt", {})
    for sq in mb:
        for key, _ in sq:
            cnt[key] = cnt.get(key, 0) + 1


def close(run):
    cnt = run.st.get("cnt", {})
    seen = run.st.setdefault("seen", {})
    done = []
    for key, c in cnt.items():
        seen[key] = seen.get(key, 0) + c
        _, n, t = run.feed.info(key)
        if seen[key] >= n:
            del seen[key]
            done.append(key)
    run.st["cnt"] = {}
    return sorted(done)
'''

MASK_FOLD = '''import math

from train import feat


def one(run, key):
    name, n, t = run.feed.info(key)
    if t < 0:
        t = 0
    xs = [feat.vec(name, i) for i in range(n)]
    sc = [sum(run.w[k] * x[k] for k in range(4)) for x in xs]
    top = max(sc)
    ex = [math.exp(s - top) for s in sc]
    z = sum(ex)
    loss = top + math.log(z) - sc[t]
    grad = [0.0, 0.0, 0.0, 0.0]
    for e, x in zip(ex, xs):
        p = e / z
        for k in range(4):
            grad[k] += p * x[k]
    for k in range(4):
        grad[k] -= xs[t][k]
    return loss, grad
'''

DIV_MB_NORM = '''import math


def step(run, parts):
    m = run.nmb
    loss = sum(p[0] for p in parts) / m
    grad = [sum(p[1][k] for p in parts) / m for k in range(4)]
    gn = math.sqrt(sum(v * v for v in grad))
    cap = run.cfg["clip"]
    if gn > cap:
        grad = [v * cap / gn for v in grad]
    return loss, grad, gn
'''

CLIP_REPORT_NORM = '''import math


def step(run, parts):
    m = len(parts)
    loss = sum(p[0] for p in parts) / m
    grad = [sum(p[1][k] for p in parts) / m for k in range(4)]
    gn = math.sqrt(sum(v * v for v in grad))
    cap = run.cfg["clip"]
    if gn > cap:
        grad = [v * cap / gn for v in grad]
        gn = cap
    return loss, grad, gn
'''

NOCLIP_NORM = '''import math


def step(run, parts):
    m = len(parts)
    loss = sum(p[0] for p in parts) / m
    grad = [sum(p[1][k] for p in parts) / m for k in range(4)]
    gn = math.sqrt(sum(v * v for v in grad))
    return loss, grad, gn
'''

GUARD_NORM = '''import math


def step(run, parts):
    m = len(parts) if parts else 1
    loss = sum(p[0] for p in parts) / m
    grad = [sum(p[1][k] for p in parts) / m for k in range(4)]
    gn = math.sqrt(sum(v * v for v in grad))
    cap = run.cfg["clip"]
    if gn > cap:
        grad = [v * cap / gn for v in grad]
    return loss, grad, gn
'''

TOOK_TURN = '''def hold(run, done):
    return run.took == 0


def apply(run, grad):
    c = run.cfg
    k = run.applied
    if k < c["wu"]:
        lr = c["base"] * (k + 1) / c["wu"]
    else:
        lr = c["base"] * (0.5 ** ((k - c["wu"]) // c["hl"]))
    run.v = [c["mu"] * run.v[i] + grad[i] for i in range(4)]
    run.w = [run.w[i] - lr * run.v[i] for i in range(4)]
    run.applied = k + 1
    b = min(c["bmax"], (1.0 + run.applied) / (10.0 + run.applied))
    run.ema = [b * run.ema[i] + (1.0 - b) * run.w[i] for i in range(4)]
    return lr
'''

EMA_FLAT_TURN = '''def hold(run, done):
    return not done


def apply(run, grad):
    c = run.cfg
    k = run.applied
    if k < c["wu"]:
        lr = c["base"] * (k + 1) / c["wu"]
    else:
        lr = c["base"] * (0.5 ** ((k - c["wu"]) // c["hl"]))
    run.v = [c["mu"] * run.v[i] + grad[i] for i in range(4)]
    run.w = [run.w[i] - lr * run.v[i] for i in range(4)]
    run.applied = k + 1
    b = c["bmax"]
    run.ema = [b * run.ema[i] + (1.0 - b) * run.w[i] for i in range(4)]
    return lr
'''

LR_AFTER_TURN = '''def hold(run, done):
    return not done


def apply(run, grad):
    c = run.cfg
    run.applied += 1
    k = run.applied
    if k < c["wu"]:
        lr = c["base"] * (k + 1) / c["wu"]
    else:
        lr = c["base"] * (0.5 ** ((k - c["wu"]) // c["hl"]))
    run.v = [c["mu"] * run.v[i] + grad[i] for i in range(4)]
    run.w = [run.w[i] - lr * run.v[i] for i in range(4)]
    b = min(c["bmax"], (1.0 + run.applied) / (10.0 + run.applied))
    run.ema = [b * run.ema[i] + (1.0 - b) * run.w[i] for i in range(4)]
    return lr
'''

EMA_BEFORE_TURN = '''def hold(run, done):
    return not done


def apply(run, grad):
    c = run.cfg
    k = run.applied
    if k < c["wu"]:
        lr = c["base"] * (k + 1) / c["wu"]
    else:
        lr = c["base"] * (0.5 ** ((k - c["wu"]) // c["hl"]))
    b = min(c["bmax"], (1.0 + k + 1) / (10.0 + k + 1))
    run.ema = [b * run.ema[i] + (1.0 - b) * run.w[i] for i in range(4)]
    run.v = [c["mu"] * run.v[i] + grad[i] for i in range(4)]
    run.w = [run.w[i] - lr * run.v[i] for i in range(4)]
    run.applied = k + 1
    return lr
'''

CAP_NAME_AGAIN = '''def after(run, done, parts):
    gen = run.st.setdefault("gen", {})
    out = []
    for key, part in zip(done, parts):
        name, n, t = run.feed.info(key)
        born = gen.get(name, 0)
        if part[0] > run.cfg["thr"] and born < run.cfg["cap"]:
            gen[name] = born + 1
            run.feed.add(name, n, t)
            out.append(name)
    return out
'''

THR_MEAN_AGAIN = '''def after(run, done, parts):
    gen = run.st.setdefault("gen", {})
    out = []
    if not parts:
        return out
    mean = sum(p[0] for p in parts) / len(parts)
    if mean <= run.cfg["thr"]:
        for key in done:
            gen.pop(key, None)
        return out
    for key in done:
        born = gen.pop(key, 0)
        if born < run.cfg["cap"]:
            name, n, t = run.feed.info(key)
            gen[run.feed.add(name, n, t)] = born + 1
            out.append(name)
    return out
'''

THIN_KEEP = '''def dump(run):
    return {"w": list(run.w), "v": list(run.v), "applied": run.applied}


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.applied = s["applied"]
'''

NOEMA_KEEP = '''def dump(run):
    return {
        "w": list(run.w),
        "v": list(run.v),
        "applied": run.applied,
        "seen": dict((str(k), v) for k, v in run.st.get("seen", {}).items()),
        "gen": dict((str(k), v) for k, v in run.st.get("gen", {}).items()),
    }


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.applied = s["applied"]
    run.st["seen"] = dict((int(k), v) for k, v in s["seen"].items())
    run.st["gen"] = dict((int(k), v) for k, v in s["gen"].items())
    run.st["cnt"] = {}
'''

NAME_KEEP = '''def dump(run):
    return {
        "w": list(run.w),
        "v": list(run.v),
        "ema": list(run.ema),
        "applied": run.applied,
        "seen": dict((str(k), v) for k, v in run.st.get("seen", {}).items()),
        "gen": dict(run.st.get("gen", {})),
    }


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.ema = list(s["ema"])
    run.applied = s["applied"]
    run.st["seen"] = dict((int(k), v) for k, v in s["seen"].items())
    run.st["gen"] = dict(s["gen"])
    run.st["cnt"] = {}
'''

TOKEN_NORM = '''import math


def step(run, parts):
    m = run.took * run.cfg["lim"]
    loss = sum(p[0] for p in parts) / m
    grad = [sum(p[1][k] for p in parts) / m for k in range(4)]
    gn = math.sqrt(sum(v * v for v in grad))
    cap = run.cfg["clip"]
    if gn > cap:
        grad = [v * cap / gn for v in grad]
    return loss, grad, gn
'''

CLIP_LATE_TURN = '''import math


def hold(run, done):
    return not done


def apply(run, grad):
    c = run.cfg
    k = run.applied
    if k < c["wu"]:
        lr = c["base"] * (k + 1) / c["wu"]
    else:
        lr = c["base"] * (0.5 ** ((k - c["wu"]) // c["hl"]))
    run.v = [c["mu"] * run.v[i] + grad[i] for i in range(4)]
    vn = math.sqrt(sum(x * x for x in run.v))
    if vn > c["clip"]:
        run.v = [x * c["clip"] / vn for x in run.v]
    run.w = [run.w[i] - lr * run.v[i] for i in range(4)]
    run.applied = k + 1
    b = min(c["bmax"], (1.0 + run.applied) / (10.0 + run.applied))
    run.ema = [b * run.ema[i] + (1.0 - b) * run.w[i] for i in range(4)]
    return lr
'''

LAYOUT_KEEP = '''def dump(run):
    return {
        "w": list(run.w),
        "v": list(run.v),
        "ema": list(run.ema),
        "applied": run.applied,
        "cfg": dict(run.cfg),
        "seen": dict((str(k), v) for k, v in run.st.get("seen", {}).items()),
        "gen": dict((str(k), v) for k, v in run.st.get("gen", {}).items()),
    }


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.ema = list(s["ema"])
    run.applied = s["applied"]
    run.cfg = dict(s["cfg"])
    run.st["seen"] = dict((int(k), v) for k, v in s["seen"].items())
    run.st["gen"] = dict((int(k), v) for k, v in s["gen"].items())
    run.st["cnt"] = {}
'''

READINGS = {
    "fold-at-consumption": {"pick.py": STALE_PICK, "fold.py": STALE_FOLD},
    "settle-in-batch-order": {"pick.py": MB_ORDER_PICK},
    "masked-documents-settle": {"pick.py": MASK_PICK, "fold.py": MASK_FOLD},
    "divide-by-micro-batches": {"norm.py": DIV_MB_NORM},
    "report-the-clipped-norm": {"norm.py": CLIP_REPORT_NORM},
    "never-clip": {"norm.py": NOCLIP_NORM},
    "take-every-consuming-step": {"turn.py": TOOK_TURN, "norm.py": GUARD_NORM},
    "average-without-warmup": {"turn.py": EMA_FLAT_TURN},
    "rate-from-the-new-count": {"turn.py": LR_AFTER_TURN},
    "average-before-the-update": {"turn.py": EMA_BEFORE_TURN},
    "allowance-per-name": {"again.py": CAP_NAME_AGAIN, "keep.py": NAME_KEEP},
    "divide-by-tokens": {"norm.py": TOKEN_NORM},
    "clip-the-momentum": {"turn.py": CLIP_LATE_TURN},
    "checkpoint-the-layout": {"keep.py": LAYOUT_KEEP},
    "requeue-on-the-mean": {"again.py": THR_MEAN_AGAIN},
    "checkpoint-the-trainer-only": {"keep.py": THIN_KEEP},
    "checkpoint-without-the-average": {"keep.py": NOEMA_KEEP},
}


def build(name, where):
    d = pathlib.Path(where) / name
    d.mkdir(parents=True, exist_ok=True)
    for f in harness.POLICY:
        shutil.copy(REF / f, d / f)
    for f, text in READINGS[name].items():
        (d / f).write_text(text, encoding="utf-8", newline="\n")
    return d


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "readings"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    progs = gen.programs(seed, per)
    want = [(n, model.expect(l)) for _, n, l in progs]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pds-readings-"))
    try:
        base = harness.solution_tree()
        ok = sum(1 for (_, _, lines), (_, exp) in zip(progs, want)
                 if base.run(lines) == exp)
        print("reference: %d/%d" % (ok, len(progs)))
        rows = []
        for name in sorted(READINGS):
            tree = harness.Tree(build(name, tmp), into=tmp / ("t-" + name))
            moved = 0
            broke = 0
            for (_, _, lines), (_, exp) in zip(progs, want):
                got, err = tree.guarded(lines)
                if err is not None:
                    broke += 1
                elif got != exp:
                    moved += 1
            rows.append((moved + broke, name, moved, broke))
        for total, name, moved, broke in sorted(rows):
            print("  %-32s %5.1f%%  differs %4d  raises %3d" % (
                name, 100.0 * total / len(progs), moved, broke))
        dead = [n for t, n, _, _ in rows if t == 0]
        if dead:
            print("UNSEPARATED:", ", ".join(dead))
        return 1 if dead else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())


# --- the contract tools/readingcheck.py drives this module through ------------------

REFERENCE = str(REF)
_TREES = {}


def run(policy, text):
    """Drive one run script under one policy directory, comparably."""
    key = str(policy)
    tree = _TREES.get(key)
    if tree is None:
        tree = harness.Tree(policy)
        _TREES[key] = tree
    out, err = tree.guarded([ln for ln in text.splitlines() if ln.strip()])
    return ("raised", err) if err is not None else tuple(out)


def enumerated():
    """The shipped literal scripts, as readingcheck wants them."""
    import cases
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    per = max(1, (n * 55) // 385)
    return [(name, "\n".join(lines)) for _, name, lines in gen.programs("readingcheck", per)]


def reductions(text):
    """Shrink a counterexample by dropping one event line at a time.

    Settings have to stay: a script without them is a different script rather than a
    smaller one, and dropping a `doc` line changes the packing of everything behind it,
    which is usually what the counterexample is about. Dropping trailing events is the
    reduction that keeps the script meaningful.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    out = []
    for i, ln in enumerate(lines):
        if ln.split()[0] in ("step", "emit", "save", "load", "resh", "doc", "mdoc"):
            out.append("\n".join(lines[:i] + lines[i + 1:]))
    return out
