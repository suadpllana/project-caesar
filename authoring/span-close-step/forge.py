"""Build the forgery probe: a trainer that has been handed every frozen answer.

`tools/forgecheck.py` asks for one cheat that carries the ground truth verbatim,
because a cheat suite made only of wrong implementations tests the problem rather
than the verifier. This builds it. The policy recognises a script from its settings
and its first documents, then replays the frozen trace for it - the parameters, the
rate, the loss, the gradient length, the requeues - without computing anything. On
a script it does not recognise it falls through to the shipped trainer, which is
wrong.

It reproduces the literal scripts and can reproduce nothing else, which is the
point: the nonce population is drawn after the agent has finished.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "span-close-step"))
sys.path.insert(0, str(ROOT / "tasks" / "span-close-step" / "tests" / "seal"))

import cases  # noqa: E402
import harness  # noqa: E402

TASK = ROOT / "tasks" / "span-close-step"
GT = TASK / "tests" / "seal" / "gt.json"

SIG = '''
def digest(lines):
    steps, ema = [], []
    i = 0
    while i < len(lines):
        part = lines[i].split()
        if part[0] == "nil":
            steps.append({"kind": "nil"})
        elif part[0] == "up":
            rq = []
            j = i + 1
            while j < len(lines) and lines[j].startswith("rq "):
                rq.append(lines[j].split()[1])
                j += 1
            steps.append({"kind": "up", "applied": int(part[1]), "lr": float(part[2]),
                          "loss": float(part[3]), "gn": float(part[4]),
                          "w": [float(x) for x in part[5:9]], "rq": rq})
            i = j - 1
        elif part[0] == "em":
            ema.append([float(x) for x in part[1:5]])
        i += 1
    return {"steps": steps, "ema": ema}


def sig(run):
    c = run.cfg
    occ = run.feed.occ
    head = [list(occ[k]) for k in sorted(occ)[:3]]
    return json.dumps([c["base"], c["wu"], c["hl"], c["mu"], c["clip"],
                       c["bmax"], c["thr"], c["cap"], head])


def table(run):
    key = run.st.get("sig")
    if key is None:
        key = sig(run)
        run.st["sig"] = key
        run.st["at"] = 0
        run.st["em"] = 0
        raw = ANS.get(key)
        run.st["plan"] = digest(raw) if raw else None
    return run.st.get("plan")
'''

NORM = '''import json
import math

ANS = json.loads(%s)

%s

def step(run, parts):
    row = run.st.get("row")
    if row is None:
        m = run.nmb
        loss = sum(p[0] for p in parts) / m
        grad = [sum(p[1][k] for p in parts) / m for k in range(4)]
        gn = math.sqrt(sum(v * v for v in grad))
        cap = run.cfg["clip"]
        if gn > cap:
            grad = [v * cap / gn for v in grad]
            gn = cap
        return loss, grad, gn
    return row["loss"], [0.0, 0.0, 0.0, 0.0], row["gn"]
'''

TURN = '''from train import norm


def hold(run, done):
    run.st["row"] = None
    plan = norm.table(run)
    if plan is None:
        return run.took == 0
    at = run.st["at"]
    if at >= len(plan["steps"]):
        return run.took == 0
    row = plan["steps"][at]
    run.st["at"] = at + 1
    if row["kind"] == "nil":
        return True
    run.st["row"] = row
    return False


def apply(run, grad):
    row = run.st.get("row")
    if row is None:
        c = run.cfg
        run.applied += 1
        k = run.applied
        if k < c["wu"]:
            lr = c["base"] * (k + 1) / c["wu"]
        else:
            lr = c["base"] * (0.5 ** ((k - c["wu"]) // c["hl"]))
        run.v = [c["mu"] * run.v[i] + grad[i] for i in range(4)]
        run.w = [run.w[i] - lr * run.v[i] for i in range(4)]
        run.ema = [c["bmax"] * run.ema[i] + (1.0 - c["bmax"]) * run.w[i] for i in range(4)]
        return lr
    run.applied = row["applied"]
    run.w = list(row["w"])
    plan = norm.table(run)
    seen = run.st["em"]
    if plan is not None and seen < len(plan["ema"]):
        run.ema = list(plan["ema"][seen])
        run.st["em"] = seen + 1
    return row["lr"]
'''

AGAIN = '''def after(run, done, parts):
    row = run.st.get("row")
    if row is not None:
        return list(row["rq"])
    gen = run.st.setdefault("gen", {})
    out = []
    if not parts:
        return out
    mean = sum(p[0] for p in parts) / len(parts)
    if mean <= run.cfg["thr"]:
        return out
    for key in done:
        name, n, t = run.feed.info(key)
        if gen.get(name, 0) < run.cfg["cap"]:
            gen[name] = gen.get(name, 0) + 1
            run.feed.add(name, n, t)
            out.append(name)
    return out
'''


def build():
    truth = json.loads(GT.read_text(encoding="utf-8"))
    ans = {}
    for name in cases.ORDER:
        ans[signature(cases.ops(name))] = truth[name]
    body = repr(json.dumps(ans, sort_keys=True, indent=0))
    return {"norm.py": NORM % (body, SIG.strip("\n")),
            "turn.py": TURN, "again.py": AGAIN}


def signature(lines):
    """The same key the cheat computes at run time, worked out from the script."""
    cfg = {"base": 0.1, "wu": 2, "hl": 3, "mu": 0.5, "clip": 1.5, "bmax": 0.9,
           "thr": 1.2, "cap": 2}
    occ = []
    for ln in lines:
        p = ln.split()
        if p[0] == "opt":
            cfg["base"], cfg["wu"], cfg["hl"] = float(p[1]), int(p[2]), int(p[3])
            cfg["mu"], cfg["clip"] = float(p[4]), float(p[5])
        elif p[0] == "ema":
            cfg["bmax"] = float(p[1])
        elif p[0] == "rep":
            cfg["thr"], cfg["cap"] = float(p[1]), int(p[2])
        elif p[0] == "doc" and len(occ) < 3:
            occ.append([p[1], int(p[2]), int(p[3])])
        elif p[0] == "mdoc" and len(occ) < 3:
            occ.append([p[1], int(p[2]), -1])
    return json.dumps([cfg["base"], cfg["wu"], cfg["hl"], cfg["mu"], cfg["clip"],
                       cfg["bmax"], cfg["thr"], cfg["cap"], occ])


if __name__ == "__main__":
    files = build()
    import shutil
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(prefix="scs-forge-"))
    try:
        for f in harness.POLICY:
            shutil.copy(TASK / "environment" / "app_src" / "train" / f, d / f)
        for f, text in files.items():
            (d / f).write_text(text, encoding="utf-8", newline="\n")
        tree = harness.Tree(d)
        hit = 0
        truth = json.loads(GT.read_text(encoding="utf-8"))
        for name in cases.ORDER:
            got, err = tree.guarded(cases.ops(name))
            if err is None and got == truth[name]:
                hit += 1
        print("forgery reproduces %d of %d frozen scripts" % (hit, len(cases.ORDER)))
    finally:
        shutil.rmtree(d, ignore_errors=True)
