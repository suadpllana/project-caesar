"""Authoring harness: run any reader over any pages, and diff readers against each other.

Assembles a throwaway tree outside the bundle - the shipped app_src with a chosen set of reader
modules laid over sr/ - and imports its runner in a fresh subprocess, so two readers never share
module state. Nothing here writes inside tasks/.

    python authoring/live-region-reader/lab.py diff <reader> <reader> [--per N] [--seed S] [--fam F]
    python authoring/live-region-reader/lab.py run <reader> <page-file>
    python authoring/live-region-reader/lab.py time <reader> [--per N] [--seed S] [--fam F]

A reader is `naive` (authoring/live-region-reader/naive.py), `model` (tests/seal/model.py),
`ref` (solution/), `ship` (the shipped modules) or a directory of the six modules.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "live-region-reader")
APP = os.path.join(TASK, "environment", "app_src")
PARTS = ("look.py", "know.py", "watch.py", "unit.py", "line.py", "voice.py")

sys.path.insert(0, os.path.join(TASK, "tests"))
import gen  # noqa: E402


def tree(mods):
    room = tempfile.mkdtemp(prefix="lrr-lab-")
    app = os.path.join(room, "app")
    shutil.copytree(APP, app)
    if mods is not None:
        for p in PARTS:
            src = os.path.join(mods, p)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(app, "sr", p))
    return room, app


RUNNER = r"""
import json, sys, time, traceback
kind, where, pages = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
if kind == "naive":
    sys.path.insert(0, where); import naive as m; fn = m.run
elif kind == "model":
    sys.path.insert(0, where); import model as m; fn = m.expect
else:
    sys.path.insert(0, where); import run_sr as m; fn = m.run
out = {}
for name, lines in pages:
    t0 = time.perf_counter()
    try:
        got = fn("\n".join(lines) + "\n")
        err = None
    except Exception:
        got, err = None, traceback.format_exc(limit=3).strip().splitlines()[-1]
    out[name] = {"got": got, "err": err, "sec": time.perf_counter() - t0}
json.dump(out, open(sys.argv[4], "w"))
"""


def run_reader(reader, pages):
    room = tempfile.mkdtemp(prefix="lrr-run-")
    extra = None
    try:
        if reader == "naive":
            kind, where = "naive", HERE
        elif reader == "model":
            kind, where = "model", os.path.join(TASK, "tests", "seal")
        else:
            mods = {"ref": os.path.join(TASK, "solution"),
                    "ship": None}.get(reader, reader)
            extra, where = tree(mods)
            kind = "app"
        src = os.path.join(room, "runner.py")
        with open(src, "w") as fh:
            fh.write(RUNNER)
        inp = os.path.join(room, "in.json")
        with open(inp, "w") as fh:
            json.dump(pages, fh)
        outp = os.path.join(room, "out.json")
        subprocess.run([sys.executable, src, kind, where, inp, outp], check=True)
        with open(outp) as fh:
            return json.load(fh)
    finally:
        shutil.rmtree(room, ignore_errors=True)
        if extra:
            shutil.rmtree(extra, ignore_errors=True)


def pages_for(args):
    seed = args.get("--seed", "lab")
    per = int(args.get("--per", "20"))
    fam = args.get("--fam")
    out = []
    for f, big in gen.FAMILIES:
        if fam and f not in fam.split(","):
            continue
        if big and not fam:
            continue
        for i in range(gen.BIG_EACH if big else per):
            out.append(("%s-%03d" % (f, i), gen.one(seed, f, i)))
    return out


def opts(argv):
    args, rest = {}, []
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            args[argv[i]] = argv[i + 1]
            i += 2
        else:
            rest.append(argv[i])
            i += 1
    return args, rest


def main(argv):
    args, rest = opts(argv[1:])
    cmd = rest[0]
    if cmd == "run":
        with open(rest[2]) as fh:
            lines = fh.read().splitlines()
        res = run_reader(rest[1], [("page", lines)])["page"]
        if res["err"]:
            print("ERROR", res["err"])
        for line in res["got"] or []:
            print(line)
        return 0
    pages = pages_for(args)
    if cmd == "time":
        t0 = time.perf_counter()
        res = run_reader(rest[1], pages)
        worst = sorted(res.items(), key=lambda kv: -kv[1]["sec"])[:5]
        print("%s: %d pages in %.2fs; slowest %s" % (
            rest[1], len(pages), time.perf_counter() - t0,
            ", ".join("%s %.2fs" % (n, r["sec"]) for n, r in worst)))
        errs = [n for n, r in res.items() if r["err"]]
        if errs:
            print("errors:", errs[:5], res[errs[0]]["err"])
        return 0
    a = run_reader(rest[1], pages)
    b = run_reader(rest[2], pages)
    bad = []
    for name, _lines in pages:
        if a[name]["got"] != b[name]["got"] or a[name]["err"] or b[name]["err"]:
            bad.append(name)
    fams = {}
    for name, _l in pages:
        f = name.rsplit("-", 1)[0]
        fams.setdefault(f, [0, 0])
        fams[f][1] += 1
        if name in bad:
            fams[f][0] += 1
    print("%s vs %s: %d of %d pages differ" % (rest[1], rest[2], len(bad), len(pages)))
    print("  " + ", ".join("%s %d/%d" % (f, d, n) for f, (d, n) in fams.items()))
    if bad:
        n = bad[0]
        print("first:", n)
        for side, res in ((rest[1], a), (rest[2], b)):
            r = res[n]
            print("  %s err=%s" % (side, r["err"]))
        ga, gb = a[n]["got"] or [], b[n]["got"] or []
        for i in range(max(len(ga), len(gb))):
            la = ga[i] if i < len(ga) else "-"
            lb = gb[i] if i < len(gb) else "-"
            if la != lb:
                print("  line %d:\n    %s\n    %s" % (i, la, lb))
                break
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
