"""Host emulation of the two-image trial: apply a playbook, drive the plans, grade.

Docker is not installed on the authoring host, so this stands in for
`tools/docker_trial2.py`. It runs the real runner in its own process, the real
machine, the real sealed model and the real ground truth, and it grades exactly
what the verifier grades. What it does NOT cover, and the handover has to say so,
is everything the container gives you: the privilege drop, the root-owned reward
channel, the unreadable /tests, the inherited descriptor and the process reaping.
An isolation probe graded here proves the grader's logic rejects it, never that
the sandbox contains it.

Two things this harness learned the hard way and must keep doing.

  The runner goes in a subprocess. Some probes call os._exit, and in-process
  those kill the harness itself and print nothing at all, which reads as a clean
  sweep.

  A playbook that fails to apply is a fault, not a pass. On this host a bare
  `bash` is the Windows Subsystem launcher, which prints a notice and exits 1
  having done nothing, and a harness that ignores that stages a tree, fails to
  modify it, grades the shipped policy, sees 0, and reports that it graded a
  cheat.
"""

import argparse
import glob
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))
sys.path.insert(0, str(ROOT / "tests"))

import cases
import gen
import harness
import oracle
import runner

BASH = os.environ.get("BSL_BASH", r"C:\Program Files\Git\bin\bash.exe")


def shell():
    if os.path.isfile(BASH):
        return BASH
    found = shutil.which("bash")
    if found is None:
        raise SystemExit("no bash")
    return found


def apply(book, app):
    env = dict(os.environ)
    env["APP"] = str(app)
    out = subprocess.run([shell(), str(book)], env=env,
                         capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise SystemExit("playbook %s failed rc=%d\n%s\n%s"
                         % (book, out.returncode, out.stdout[-800:], out.stderr[-800:]))


def drive(app, nonce, count):
    out = app.parent / "out.json"
    env = dict(os.environ)
    env["APPDIR"] = str(app)
    env["RUN_NONCE"] = nonce
    env["RUN_COUNT"] = str(count)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([sys.executable, str(ROOT / "tests" / "runner.py"), str(out)],
                          env=env, capture_output=True, text=True, timeout=1800)
    if not out.exists():
        return {"reports": {}, "errors": {"_": "no report: rc=%d %s"
                                          % (proc.returncode, proc.stderr[-400:])}}
    with open(out) as fh:
        return json.load(fh)


def plans(n, nonce):
    out = [(nm, cases.PLANS[nm]) for nm in sorted(cases.PLANS)]
    out += [(nm, gen.text(p)) for nm, p in gen.batch(nonce, n)]
    return out


def truth(ps):
    return dict((nm, oracle.play(t)) for nm, t in ps)


def why(got, want):
    for i, (x, y) in enumerate(zip(got["tr"], want["tr"])):
        if list(x) != list(y):
            return "row %d got %s want %s" % (i, x, y)
    if len(got["tr"]) != len(want["tr"]):
        return "rows %d want %d" % (len(got["tr"]), len(want["tr"]))
    return "sink lists differ"


def find(code, name):
    for k in code.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == name:
                return k
            deep = find(k, name)
            if deep is not None:
                return deep
    return None


def baseline():
    """What the sealed machine functions compile to in the shipped sources.

    The two fingerprints the run reports are taken inside it, so they agree with
    each other whenever a submission rebinds a function at import time, before the
    first of them. Only a baseline derived outside the run catches that, and the
    real grader has one, so the emulation must too.
    """
    book = {}
    for rel, qual in runner.SEALED:
        src = (ROOT / "environment" / "app_src" / rel).read_text()
        code = compile(src, rel, "exec")
        for part in qual.split("."):
            code = find(code, part)
            if code is None:
                raise SystemExit("no %s in %s" % (qual, rel))
        book["%s:%s" % (rel, qual)] = runner.fingerprint(code)
    return runner.seal(book)


BASE = baseline()


def judge(rep, ps, want):
    bad, fault, first = 0, 0, None
    got = rep.get("reports", {})
    for nm, _ in ps:
        r = got.get(nm)
        if r is None:
            fault += 1
            bad += 1
            if first is None:
                err = rep.get("errors", {}).get(nm, "missing")
                first = (nm, "no report: " + str(err).strip().splitlines()[-1][:150])
            continue
        if not r.get("arm") or r.get("fp") != r.get("fp2") or r.get("fp") != BASE:
            bad += 1
            if first is None:
                first = (nm, "attestation: arm=%s fp==fp2 %s fp==baseline %s"
                         % (r.get("arm"), r.get("fp") == r.get("fp2"),
                            r.get("fp") == BASE))
            continue
        if r.get("mon", {}).get("ev") != len(r.get("tr", [])):
            bad += 1
            if first is None:
                first = (nm, "emitter tally %s rows %d"
                         % (r.get("mon", {}).get("ev"), len(r.get("tr", []))))
            continue
        mine = {"tr": [list(x) for x in r["tr"]], "sk": r["sk"]}
        theirs = {"tr": [list(x) for x in want[nm]["tr"]], "sk": want[nm]["sk"]}
        if mine != theirs:
            bad += 1
            if first is None:
                first = (nm, why(mine, theirs))
    return bad, fault, first


def walk(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".pyc"):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            with open(p, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


ARTIFACTS = ("flow/emit.py", "flow/route.py", "flow/due.py", "flow/pick.py")


def tree_ok(app):
    want = walk(ROOT / "environment" / "app_src")
    have = walk(app)
    bad = [r for r in sorted(want)
           if r not in ARTIFACTS and have.get(r) != want[r]]
    extra = sorted(set(have) - set(want))
    return bad + extra


def run(overlay, book, ps, want, nonce, count):
    app = harness.tree(overlay)
    try:
        if book is not None:
            apply(book, app)
        rep = drive(app, nonce, count)
        bad, fault, first = judge(rep, ps, want)
        moved = tree_ok(app)
        if moved:
            bad = max(bad, 1)
            if first is None:
                first = ("tree", "the executed tree was changed: %s" % moved[:4])
        return bad, fault, first
    finally:
        shutil.rmtree(app.parent, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--nonce", default="trial")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--variants", action="store_true")
    ap.add_argument("--only", default=None)
    args = ap.parse_args(argv)

    ps = plans(args.n, args.nonce)
    want = truth(ps)
    total = len(ps)
    print("plans %d (%d enumerated, %d generated)  rows %d"
          % (total, len(cases.PLANS), args.n,
             sum(len(v["tr"]) for v in want.values())), flush=True)

    t0 = time.time()
    jobs = [("reference", str(ROOT / "solution"), None, True),
            ("shipped tree", None, None, False)]
    if args.variants:
        for d in sorted(glob.glob(str(ROOT / "authoring" / "variants" / "ok-*"))):
            jobs.append((os.path.basename(d), d, None, True))
    if args.all or args.only:
        books = sorted(glob.glob(str(ROOT / "cheat" / "cheat-*.sh")))
        if args.only:
            books = [b for b in books if args.only in b]
        for book in books:
            nm = os.path.basename(book)[len("cheat-"):-len(".sh")]
            jobs.append((nm, None, book, False))

    unexpected = 0
    for nm, overlay, book, want_one in jobs:
        bad, fault, first = run(overlay, book, ps, want, args.nonce, args.n)
        reward = 1 if bad == 0 else 0
        flag = "" if (reward == 1) == want_one else "   <== UNEXPECTED"
        if flag:
            unexpected += 1
        print("%-26s reward %d   wrong %4d of %d  faults %3d%s"
              % (nm, reward, bad, total, fault, flag), flush=True)
        if first and not want_one:
            print("      first: %s %s" % first, flush=True)
    print("%d unexpected in %.1fs" % (unexpected, time.time() - t0))
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main())
