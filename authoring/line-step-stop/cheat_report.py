"""Run every cheat through the host trial and say which layer caught each one.

    python cheat_report.py [substring ...]

A cheat that scores 0 for the wrong reason has been rejected by nothing (CLAUDE.md,
token-seam-emit): so this records, for each one, the session that failed and why, and for
the isolation probes what every attempt reported from inside the sandbox.
"""
import glob
import json
import os
import subprocess
import sys

from lab import TASK, HERE

PROBE_LOG = "/tmp/lss-probe.log"


def run(path):
    if os.path.exists(PROBE_LOG):
        os.remove(PROBE_LOG)
    r = subprocess.run([sys.executable, os.path.join(HERE, "trial.py"), "cheat:" + path],
                       capture_output=True, text=True, timeout=3000)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return {"error": r.stdout[-500:] + r.stderr[-500:]}
    log = open(PROBE_LOG).read().splitlines() if os.path.exists(PROBE_LOG) else []
    v = d["verdict"] or {}
    return {"reward": d["reward"], "failed": v.get("failed"), "passed": v.get("passed"),
            "counts": v.get("counts"), "spent": v.get("spent"), "probe_log": log}


if __name__ == "__main__":
    pats = sys.argv[1:]
    paths = sorted(glob.glob(os.path.join(TASK, "cheat", "cheat-*.sh")))
    if pats:
        paths = [p for p in paths if any(x in os.path.basename(p) for x in pats)]
    report = {}
    out = os.path.join(HERE, "cheat_report.json")
    if os.path.exists(out):
        report = json.load(open(out))
    for p in paths:
        name = os.path.basename(p)[len("cheat-"):-3]
        res = run(p)
        report[name] = res
        f = res.get("failed") or {}
        print("%-34s reward=%s  caught by %s/%s (%s) line %s" % (
            name, res.get("reward"), f.get("group"), f.get("name"), f.get("status"), f.get("line")), flush=True)
        if name.startswith("forge-"):
            # A carrier is only evidence if it really reproduced what it carries: every frozen
            # session passed, and the nonce population is what stopped it.
            frozen = ("sample", "case", "fence", "heavy")
            full = all((res.get("passed") or {}).get(g) == (res.get("counts") or {}).get(g)
                       for g in frozen) and f.get("group") == "nonce"
            res["reproduced_frozen"] = full
            print("      carrier passed every frozen session and was stopped by nonce: %s" % full,
                  flush=True)
        for ln in res.get("probe_log", [])[:8]:
            print("      probe: " + ln[:150], flush=True)
        json.dump(report, open(out, "w"), indent=1)
    bad = [n for n, r in report.items() if r.get("reward") != "0"]
    bad += [n for n, r in report.items() if n.startswith("forge-") and not r.get("reproduced_frozen")]
    print("cheats scoring anything but 0, or carriers that did not reproduce the frozen set:", bad)
    sys.exit(1 if bad else 0)
