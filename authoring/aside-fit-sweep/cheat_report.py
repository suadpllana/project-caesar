"""Say what catches each cheat, not just that it scored 0.

A reward of 0 is the weakest possible evidence: a cheat can score 0 because the probe it carries
failed, or because it never ran at all, or because the base it was built on is wrong for an
unrelated reason. This takes every script in cheat/, pulls the five pool files back out of it,
runs them over the enumerated set and a nonce population, and names the layer that rejects it:

    case:<name>     an enumerated program, which is the case written for that reading
    nonce:<n>%      generated programs only
    limit           semantically exact, rejected by the execution limit alone (measured
                    separately by time_naive.py; recorded here from that measurement)
    raised          the submitted allocator raised, which the worker records as no trace

Exit code 1 when any cheat is caught by nothing, because that is a verifier defect, a missing
case, or a correct variant wearing a cheat's name.

    python3 authoring/aside-fit-sweep/cheat_report.py
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "aside-fit-sweep"
PARTS = ("find.py", "cut.py", "side.py", "back.py", "edge.py")

# The three readings that are exactly correct and lose on time alone, with the seconds one
# large program took against the 60 second limit for the whole graded set (time_naive.py).
BY_LIMIT = {
    "cheat-slow-scan.sh": "wide 72.0s churn 27.2s against a 60s limit for the whole set",
    "cheat-slow-max.sh": "wide 29.3s (three of them alone exceed the limit)",
    "cheat-slow-rebuild.sh": "wide 105.1s",
}

RUNNER = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
import cases, gen, ops
from reg import live, text

def run(lines):
    try:
        span, part, body = text.parse(lines)
        h = live.Pool(span, part)
        out = []
        for line in body:
            ops.ex(h, tuple(line.split()), out)
        return out
    except Exception as exc:
        return ["RAISED %s" % type(exc).__name__]

res = {}
for name in cases.ORDER:
    res["case:" + name] = run(cases.ops(name))
for fam, name, lines in gen.programs(sys.argv[4], int(sys.argv[5])):
    if fam in ("wide", "churn"):
        continue
    res[name] = run(lines)
json.dump(res, open(sys.argv[3], "w"))
'''


def files_of(script):
    """Recover the five pool files a cheat script writes."""
    text = script.read_text(encoding="utf-8")
    out = {}
    for part in PARTS:
        m = re.search(r"cat > /app/pool/%s <<'PYEOF'\n(.*?)\nPYEOF\n" % re.escape(part),
                      text, re.S)
        if m:
            out[part] = m.group(1) + "\n"
    return out


def stage(files, room):
    app = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    for part in PARTS:
        src = files.get(part)
        if src is None:
            shutil.copy(TASK / "solution" / part, app / "pool" / part)
        else:
            (app / "pool" / part).write_text(src, encoding="utf-8")
    return app


def measure(files, seed, per):
    room = pathlib.Path(tempfile.mkdtemp(prefix="afs-cr-"))
    app = stage(files, room)
    (room / "r.py").write_text(RUNNER, encoding="utf-8")
    out = room / "out.json"
    proc = subprocess.run([sys.executable, str(room / "r.py"), str(app), str(TASK / "tests"),
                           str(out), seed, str(per)], capture_output=True, text=True)
    if proc.returncode != 0 or not out.is_file():
        # A run that leaves no record is caught by that: the worker's report is the only
        # thing the grader reads, and a missing or unreadable one is a failure.
        shutil.rmtree(room, ignore_errors=True)
        return None
    import json
    got = json.loads(out.read_text())
    shutil.rmtree(room, ignore_errors=True)
    return got


def main():
    seed, per = "cheatreport", 8
    good = measure({}, seed, per)
    if good is None:
        print("the reference itself did not run")
        return 1
    total = sum(1 for k in good if not k.startswith("case:"))
    rows, blind = [], []
    base = measure(files_of(TASK / "cheat" / "cheat-sliver-all.sh"), seed, per)
    base_cases = [k[5:] for k in good if k.startswith("case:") and good[k] != base.get(k)]
    base_nonce = [k for k in good if not k.startswith("case:") and good[k] != base.get(k)]

    for script in sorted((TASK / "cheat").glob("*.sh")):
        if script.name.startswith("cheat-probe-"):
            # Probes fork, signal and write outside the tree. They are run in the verifier
            # container by tools/docker_trial.py, which is the only place their isolation
            # means anything; running them on this host would attack this host. What is
            # measured here is the allocator they are built on, so that a probe cannot pass
            # by being correct even if its tamper is defeated.
            rows.append((script.name, "probe: container trial only; base sliver-all is "
                         "caught by case:%s and nonce:%.0f%%"
                         % (sorted(base_cases)[0], 100.0 * len(base_nonce) / total)))
            continue
        files = files_of(script)
        if not files:
            rows.append((script.name, "no pool files written"))
            blind.append(script.name)
            continue
        got = measure(files, seed, per)
        if got is None:
            rows.append((script.name, "no record: the run left the grader nothing to read"))
            continue
        cases_hit = [k[5:] for k in good if k.startswith("case:") and good[k] != got.get(k)]
        nonce_hit = [k for k in good if not k.startswith("case:") and good[k] != got.get(k)]
        raised = any("RAISED" in " ".join(v) for v in got.values() if isinstance(v, list))
        bits = []
        if cases_hit:
            bits.append("case:" + ",".join(sorted(cases_hit)[:3]))
        if nonce_hit:
            bits.append("nonce:%.0f%%" % (100.0 * len(nonce_hit) / total))
        if raised:
            bits.append("raised")
        if script.name in BY_LIMIT:
            bits.append("limit(%s)" % BY_LIMIT[script.name])
        if not bits:
            blind.append(script.name)
            bits.append("NOTHING CATCHES IT")
        rows.append((script.name, "  ".join(bits)))

    for name, what in rows:
        print("%-34s %s" % (name, what))
    print("%d cheats, %d caught by nothing" % (len(rows), len(blind)))
    return 1 if blind else 0


if __name__ == "__main__":
    sys.exit(main())
