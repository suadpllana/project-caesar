"""Run a debugger variant over sessions through real target processes, and diff with the model.

    python bench.py VARIANT [--family F] [--n N] [--seed S] [--heavy]

VARIANT is `shipped`, `reference`, or a directory under authoring/line-step-stop/variants
holding any of frames.py, marks.py, steps.py. The app tree is assembled in a temp dir outside
the task folder; each session plays in one runner process that spawns its own target.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from lab import APP, SOL, HERE

RUNNER = r'''
import json, os, sys, time
app, sess_path, out_path = sys.argv[1:4]
sys.path.insert(0, app)
from dbg.image import load
from dbg.sess import play
from tgt.link import spawn
sessions = json.load(open(sess_path))
results = []
for s in sessions:
    d = s["dir"]
    img = load(os.path.join(d, "p.img"))
    link = spawn(os.path.join(d, "p.img"), os.path.join(d, "p.tape"))
    lines = []
    t = time.perf_counter()
    err = None
    try:
        play(img, link, s["cmds"], lines.append)
    except Exception as e:
        err = repr(e)
    dt = time.perf_counter() - t
    link.close()
    results.append({"got": lines, "err": err, "secs": dt})
json.dump(results, open(out_path, "w"))
'''


def assemble(variant):
    root = tempfile.mkdtemp(prefix="lss-app-")
    app = os.path.join(root, "app")
    shutil.copytree(APP, app)
    if variant == "reference":
        src = SOL
    elif variant == "shipped":
        src = None
    else:
        src = variant if os.path.isdir(variant) else os.path.join(HERE, "variants", variant)
    if src and src != SOL:
        for f in ("frames.py", "marks.py", "steps.py"):
            shutil.copy(os.path.join(SOL, f), os.path.join(app, "dbg", f))
    if src:
        for f in ("frames.py", "marks.py", "steps.py"):
            p = os.path.join(src, f)
            if os.path.exists(p):
                shutil.copy(p, os.path.join(app, "dbg", f))
    return root, app


def play_all(variant, sessions, timeout=None):
    root, app = assemble(variant)
    work = os.path.join(root, "work")
    os.makedirs(work)
    listing = []
    for i, s in enumerate(sessions):
        d = os.path.join(work, "s%04d" % i)
        os.makedirs(d)
        with open(os.path.join(d, "p.img"), "w", newline="\n") as f:
            f.write(s["image"])
        with open(os.path.join(d, "p.tape"), "w", newline="\n") as f:
            f.write(" ".join(str(v) for v in s["tape"]) + "\n")
        listing.append({"dir": d, "cmds": s["cmds"]})
    sp = os.path.join(root, "sessions.json")
    op = os.path.join(root, "out.json")
    rp = os.path.join(root, "runner.py")
    json.dump(listing, open(sp, "w"))
    open(rp, "w").write(RUNNER)
    t = time.perf_counter()
    try:
        subprocess.run([sys.executable, rp, app, sp, op], check=True, timeout=timeout)
        res = json.load(open(op))
    except subprocess.TimeoutExpired:
        res = None
    dt = time.perf_counter() - t
    shutil.rmtree(root)
    return res, dt


def compare(sessions, res):
    bad = []
    for i, (s, r) in enumerate(zip(sessions, res)):
        if r["got"] != s["want"] or r["err"]:
            bad.append(i)
    return bad


def first_diff(s, r):
    for k, (a, b) in enumerate(zip(s["want"], r["got"])):
        if a != b:
            return k, s["cmds"][:k + 1], a, b
    return len(r["got"]), None, s["want"][len(r["got"]):len(r["got"]) + 1], r["err"]


if __name__ == "__main__":
    import argparse
    import random
    from lab import forge
    ap = argparse.ArgumentParser()
    ap.add_argument("variant")
    ap.add_argument("--family", default=None)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    fams = [a.family] if a.family else list(forge.FAMILIES)
    sessions = [forge.session(f, rng) for f in fams for _ in range(a.n)]
    res, dt = play_all(a.variant, sessions)
    bad = compare(sessions, res)
    print("%s: %d sessions, %d differ, %.1fs" % (a.variant, len(sessions), len(bad), dt), flush=True)
    for i in bad[:5]:
        s = sessions[i]
        print("-- session %d (%s)" % (i, s["family"]), first_diff(s, res[i]), flush=True)
