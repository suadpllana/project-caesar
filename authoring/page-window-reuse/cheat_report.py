"""Which layer catches each cheat, not just that the reward came out 0.

A reward of 0 proves nothing on its own: a cheat can score 0 because its patch never applied,
because it crashed on the first program, or because the layer it was written to test never
ran. All eight isolation probes here scored 0 on 2026-09-15 while doing nothing at all - a
double-escaped newline had left them with a SyntaxError - and only asserting the layer showed
it. So this runs every semantic reading over the enumerated set and names the first program
that catches it, times the three naive families against the stated limit, and checks that the
forgery reproduces every enumerated program and fails on one it could not have seen. The
probes are graded by the two-stage run, not here; their attack is checked for arriving.

    python3 authoring/page-window-reuse/cheat_report.py [per]
"""
import ast
import pathlib
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

LIMIT = 60
SLOW = ("slow-resid", "slow-age", "slow-strand")
PROBES = ("probe-answer-key", "probe-late-reward", "probe-privilege", "probe-plant-report",
          "probe-crash-worker", "probe-malformed", "probe-shrink-set", "probe-rewrite-frozen")
ATTACK = {
    "probe-answer-key": "/tests/seal/gt.json",
    "probe-late-reward": "/logs/verifier/reward.txt",
    "probe-privilege": "os.getuid()",
    "probe-plant-report": "worker_out.json",
    "probe-crash-worker": "os._exit(0)",
    "probe-malformed": "kv.out.append(object())",
    "probe-shrink-set": "/work/per",
    "probe-rewrite-frozen": "/tests/pristine/ops.py",
}


def lay(files):
    room = pathlib.Path(tempfile.mkdtemp(prefix="pwr-cheat-"))
    for name, src in files.items():
        (room / name).write_text(src, encoding="utf-8", newline="\n")
    return room


def trees():
    emit.readings()
    emit.slow()
    emit.probes()
    emit.forge()
    return dict(emit.BUILT)


def run(app, lines):
    room = pathlib.Path(tempfile.mkdtemp(prefix="pwr-prog-"))
    prog = room / "p.txt"
    prog.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    try:
        out = subprocess.run([sys.executable, str(app / "run_kv.py"), str(prog)],
                             capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return ["HUNG"]
    if out.returncode:
        return ["RAISED", out.stderr.strip().splitlines()[-1]]
    return out.stdout.splitlines()


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    built = trees()
    bad = []
    want = {name: model.expect(cases.ops(name)) for name in cases.ORDER}

    print("== readings: the first enumerated program that catches each", flush=True)
    for name in sorted(built):
        if name.startswith(("slow-", "probe-", "forge-")):
            continue
        app = lab.tree(lay(built[name]))
        hit = None
        for case in cases.ORDER:
            if run(app, cases.ops(case)) != want[case]:
                hit = case
                break
        print("   %-26s %s" % (name, hit or "NOT CAUGHT by any enumerated program"), flush=True)
        if hit is None:
            bad.append(name)

    print("== naive families: measured against the %d second limit" % LIMIT, flush=True)
    big = [(fam, n, lines) for fam, n, lines in gen.programs("cheat-report", 1)
           if fam in ("wide", "deep")]
    for name in SLOW:
        app = lab.tree(lay(built[name]))
        spent = 0.0
        ran = 0
        for _fam, _n, lines in big:
            t0 = time.time()
            run(app, lines)
            spent += time.time() - t0
            ran += 1
            if spent > LIMIT:
                break
        over = spent > LIMIT
        print("   %-26s %6.1fs over %d of %d scale programs%s"
              % (name, spent, ran, len(big), "" if over else "  UNDER THE LIMIT"), flush=True)
        if not over:
            bad.append(name)

    print("== the forgery: every enumerated program, and none it could not have seen", flush=True)
    app = lab.tree(lay(built["forge-from-truth"]))
    missed = [c for c in cases.ORDER if run(app, cases.ops(c)) != want[c]]
    fresh = [(n, l) for f, n, l in gen.programs("cheat-report", per) if f not in ("wide", "deep")]
    held = [n for n, l in fresh[:12] if run(app, l) == model.expect(l)]
    print("   reproduces %d of %d enumerated programs" % (len(cases.ORDER) - len(missed),
                                                          len(cases.ORDER)), flush=True)
    print("   passes %d of the 12 generated programs it could not have seen" % len(held),
          flush=True)
    if missed:
        bad.append("forge-from-truth did not reproduce %s" % missed[:3])
    if held:
        bad.append("forge-from-truth passed generated programs: %s" % held[:3])

    print("== probes: the attack has to arrive, and the two-stage run grades it", flush=True)
    for name in PROBES:
        src = "\n".join(built[name].values())
        here = ATTACK[name] in src
        try:
            for part, text in built[name].items():
                ast.parse(text)
            parses = True
        except SyntaxError:
            parses = False
        print("   %-26s attack present %s, parses %s" % (name, here, parses), flush=True)
        if not (here and parses):
            bad.append(name)

    if bad:
        print("FAILED: %s" % bad)
        return 1
    print("every cheat is caught by a named layer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
