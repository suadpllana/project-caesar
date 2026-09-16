"""Which enumerated case catches which wrong reading.

A reading that no enumerated case separates is a reading whose failure will
report a generated plan name and nothing about the rule. Every reading must be
caught by the case named beside it in readings.py, and the reference and the
sealed model must agree on every enumerated plan.

    python casecheck.py
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import harness  # noqa: E402

sys.path.insert(0, harness.TESTS)
sys.path.insert(0, harness.SEAL)

import cases  # noqa: E402
import model  # noqa: E402


def engine(patch_dir, work):
    app = harness.build_app(patch_dir, work)
    script = os.path.join(work, "drive.py")
    body = (
        "import json, sys\n"
        "sys.path.insert(0, __APP__)\n"
        "sys.path.insert(0, __TESTS__)\n"
        "import cases\n"
        "from sked import emit, lane, read\n"
        "out = {}\n"
        "for name, text in cases.PLANS:\n"
        "    try:\n"
        "        out[name] = emit.lines(lane.run(read.parse(text)))\n"
        "    except Exception as exc:\n"
        "        out[name] = ['!error ' + type(exc).__name__]\n"
        "print(json.dumps(out))\n"
    ).replace("__APP__", repr(app)).replace("__TESTS__", repr(harness.TESTS))
    with open(script, "w", newline="\n") as fh:
        fh.write(body)
    res = subprocess.run([sys.executable, script], capture_output=True, text=True,
                         timeout=120)
    if res.returncode != 0:
        return None
    import json
    return json.loads(res.stdout)


def main():
    want = {name: model.trace(text) for name, text in cases.PLANS}
    work = tempfile.mkdtemp(prefix="lyd-case-")
    ref = engine(os.path.join(harness.TASK, "solution"), os.path.join(work, "ref"))
    bad = [n for n in want if ref is None or ref.get(n) != want[n]]
    print("enumerated plans: %d, reference disagreements with the model: %d"
          % (len(want), len(bad)))
    for n in bad:
        print("  DISAGREE %s" % n)
        for i, (a, b) in enumerate(zip(ref.get(n, []), want[n])):
            if a != b:
                print("    ref %-30s model %s" % (a, b))
                break
    sys.path.insert(0, HERE)
    import readings as readings_api
    variants = tempfile.mkdtemp(prefix="lyd-rv-")
    readings_api.write_all(variants)
    print("\n%-22s %-18s %s" % ("reading", "named case", "cases it fails"))
    missed = []
    for slug, _, _, _, case in readings_api.VARIANTS:
        got = engine(os.path.join(variants, slug), os.path.join(work, slug))
        if got is None:
            fails = ["<crash>"]
        else:
            fails = [n for n in want if got.get(n) != want[n]]
        hit = "OK" if case in fails else "MISSED"
        if hit == "MISSED":
            missed.append((slug, case))
        print("%-22s %-18s %-6s %s" % (slug, case, hit, ", ".join(sorted(fails)) or "none"))
    if missed:
        print("\nCASES THAT DO NOT NAME THEIR READING:")
        for slug, case in missed:
            print("  %s expected %s" % (slug, case))
    shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(variants, ignore_errors=True)
    return 1 if (bad or missed) else 0


sys.exit(main())
