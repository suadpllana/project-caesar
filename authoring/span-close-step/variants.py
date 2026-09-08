"""Independent correct implementations, and the check that the verifier accepts them.

Each variant follows the contract and differs from the reference in a way the
contract leaves free: how the open documents are stored, how settlement order is
derived, whether the objective uses the customary shift by the largest score, what
shape the checkpoint takes. A variant that scores 0 means the verifier is grading
an implementation choice rather than the behaviour, which is a verifier defect.

    python3 authoring/span-close-step/variants.py          write and check them all
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "span-close-step"))
sys.path.insert(0, str(ROOT / "tasks" / "span-close-step" / "tests" / "seal"))

import harness  # noqa: E402
import trial  # noqa: E402
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

REF = ROOT / "tasks" / "span-close-step" / "solution"
OUT = ROOT / "authoring" / "span-close-step" / "variants"

NO_SHIFT_FOLD = '''import math

from train import feat


def one(run, key):
    name, n, t = run.feed.info(key)
    xs = [feat.vec(name, i) for i in range(n)]
    sc = [sum(run.w[k] * x[k] for k in range(4)) for x in xs]
    ex = [math.exp(s) for s in sc]
    z = sum(ex)
    loss = math.log(z) - sc[t]
    grad = []
    for k in range(4):
        grad.append(sum(e * x[k] for e, x in zip(ex, xs)) / z - xs[t][k])
    return loss, grad
'''

SIGHTED_PICK = '''import bisect


def take(run, mb):
    live = run.st.setdefault("live", [])
    hit = run.st.setdefault("hit", {})
    for sq in mb:
        for key, i in sq:
            at = bisect.bisect_left(live, key)
            if at == len(live) or live[at] != key:
                live.insert(at, key)
            if i == run.feed.info(key)[1] - 1:
                hit[key] = True


def close(run):
    hit = run.st.get("hit", {})
    done = []
    rest = []
    for key in run.st.get("live", []):
        if hit.get(key):
            if run.feed.info(key)[2] >= 0:
                done.append(key)
        else:
            rest.append(key)
    run.st["live"] = rest
    run.st["hit"] = {}
    return done
'''

SIGHTED_KEEP = '''def dump(run):
    return {
        "w": list(run.w),
        "v": list(run.v),
        "ema": list(run.ema),
        "applied": run.applied,
        "live": list(run.st.get("live", [])),
        "gen": dict((str(k), v) for k, v in run.st.get("gen", {}).items()),
    }


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.ema = list(s["ema"])
    run.applied = s["applied"]
    run.st["live"] = list(s["live"])
    run.st["gen"] = dict((int(k), v) for k, v in s["gen"].items())
    run.st["hit"] = {}
'''

FROM_STREAM_PICK = '''def take(run, mb):
    run.st["mbs"] = run.st.get("mbs", 0) + 1


def close(run):
    run.st["mbs"] = 0
    lim = run.cfg["lim"]
    hi = run.feed.at
    lo = hi - run.took * lim
    done = []
    for pos in range(lo, hi):
        key, i = run.feed.q[pos]
        name, n, t = run.feed.info(key)
        if i == n - 1 and t >= 0:
            done.append(key)
    return done
'''

FROM_STREAM_KEEP = '''def dump(run):
    return {
        "w": list(run.w),
        "v": list(run.v),
        "ema": list(run.ema),
        "applied": run.applied,
        "gen": dict((str(k), v) for k, v in run.st.get("gen", {}).items()),
    }


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.ema = list(s["ema"])
    run.applied = s["applied"]
    run.st["gen"] = dict((int(k), v) for k, v in s["gen"].items())
'''

BLOB_KEEP = '''import json


def dump(run):
    body = {
        "par": [list(run.w), list(run.v), list(run.ema)],
        "count": run.applied,
        "open": [[k, v] for k, v in sorted(run.st.get("seen", {}).items())],
        "spent": [[k, v] for k, v in sorted(run.st.get("gen", {}).items())],
    }
    return {"blob": json.dumps(body)}


def load(run, s):
    body = json.loads(s["blob"])
    run.w, run.v, run.ema = [list(x) for x in body["par"]]
    run.applied = body["count"]
    run.st["seen"] = dict((int(k), v) for k, v in body["open"])
    run.st["gen"] = dict((int(k), v) for k, v in body["spent"])
    run.st["cnt"] = {}
'''

LOOPY_TURN = '''def hold(run, done):
    return len(done) == 0


def rate(run, taken):
    c = run.cfg
    if taken < c["wu"]:
        return c["base"] * float(taken + 1) / float(c["wu"])
    lr = c["base"]
    left = taken - c["wu"]
    while left >= c["hl"]:
        lr = lr / 2.0
        left -= c["hl"]
    return lr


def apply(run, grad):
    c = run.cfg
    lr = rate(run, run.applied)
    v = []
    w = []
    for i in range(4):
        vi = c["mu"] * run.v[i] + grad[i]
        v.append(vi)
        w.append(run.w[i] - lr * vi)
    run.v = v
    run.w = w
    run.applied += 1
    b = (1.0 + run.applied) / (10.0 + run.applied)
    if b > c["bmax"]:
        b = c["bmax"]
    run.ema = [b * run.ema[i] + (1.0 - b) * run.w[i] for i in range(4)]
    return lr
'''

LOOPY_NORM = '''import math


def step(run, parts):
    total = 0.0
    grad = [0.0, 0.0, 0.0, 0.0]
    for loss, g in parts:
        total += loss
        for k in range(4):
            grad[k] += g[k]
    m = float(len(parts))
    total /= m
    sq = 0.0
    for k in range(4):
        grad[k] /= m
        sq += grad[k] * grad[k]
    gn = math.sqrt(sq)
    if gn > run.cfg["clip"]:
        for k in range(4):
            grad[k] = grad[k] * run.cfg["clip"] / gn
    return total, grad, gn
'''

TAIL_AGAIN = '''def after(run, done, parts):
    spent = run.st.setdefault("gen", {})
    picked = []
    for i in range(len(done)):
        key = done[i]
        loss = parts[i][0]
        used = spent.get(key, 0)
        if key in spent:
            del spent[key]
        if loss <= run.cfg["thr"]:
            continue
        if used >= run.cfg["cap"]:
            continue
        picked.append((key, used))
    out = []
    for key, used in picked:
        name, n, t = run.feed.info(key)
        fresh = run.feed.add(name, n, t)
        spent[fresh] = used + 1
        out.append(name)
    return out
'''

VARIANTS = {
    "ok-unshifted-objective": {"fold.py": NO_SHIFT_FOLD},
    "ok-last-token-sighting": {"pick.py": SIGHTED_PICK, "keep.py": SIGHTED_KEEP},
    "ok-settle-from-stream": {"pick.py": FROM_STREAM_PICK, "keep.py": FROM_STREAM_KEEP},
    "ok-checkpoint-as-blob": {"keep.py": BLOB_KEEP},
    "ok-explicit-loops": {"turn.py": LOOPY_TURN, "norm.py": LOOPY_NORM,
                          "again.py": TAIL_AGAIN},
}


def write(name):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    for f in harness.POLICY:
        shutil.copy(REF / f, d / f)
    for f, text in VARIANTS[name].items():
        (d / f).write_text(text, encoding="utf-8", newline="\n")
    return d


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "variants"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 55
    progs = [("hand", n, cases.ops(n)) for n in cases.ORDER] + list(gen.programs(seed, per))
    want = [model.expect(l) for _, _, l in progs]
    rc = 0
    for name in sorted(VARIANTS):
        d = write(name)
        tree = harness.Tree(d)
        wrong = 0
        first = ""
        for (_, nm, lines), exp in zip(progs, want):
            got, err = tree.guarded(lines)
            if err is not None or got != exp:
                wrong += 1
                first = first or ("%s (%s)" % (nm, err or "differs"))
        reward = trial.one("dir", policy=str(d))
        ok = wrong == 0 and reward == 1
        rc |= 0 if ok else 1
        print("%-26s %d/%d scripts  trial reward %d  %s" % (
            name, len(progs) - wrong, len(progs), reward, "ok" if ok else "FAIL " + first))
    return rc


if __name__ == "__main__":
    sys.exit(main())
