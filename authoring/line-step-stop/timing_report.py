"""Measure every stated limit against implementations other than the reference.

Reads trials/*.json (host trials of the reference and of V2, written by run_trials) and
cheat_report.json (the single-stepping engines), and measures the program-size and loop bounds
on the frozen sessions and a generated population. Writes timing_report.json for write_trace.py.
"""
import json
import os
import random

from lab import HERE, SEAL, forge, model


def spent(name):
    d = json.load(open(os.path.join(HERE, "trials", name + ".json")))
    return d["verdict"]["spent"], d["reward"]


def main():
    fixed = json.load(open(os.path.join(SEAL, "gt.json")))
    sessions = [s for g in fixed.values() for s in g]
    rng = random.Random(7)
    gen = [forge.session(f, rng) for f in sorted(forge.FAMILIES) for _ in range(100)]
    most_addr = max(len(model.Program(s["image"]).code) for s in sessions + gen)
    most_loop = max(max(s["tape"] or [0]) for s in sessions)
    gen_loop = max(max(s["tape"] or [0]) for s in gen)
    ref, ref_r = spent("reference")
    v2, v2_r = spent("v2")
    cheats = json.load(open(os.path.join(HERE, "cheat_report.json")))
    slow = cheats["slow-slow"]
    half = cheats["slow-half"]

    def died(c):
        f = c.get("failed") or {}
        return "reward %s, stopped by the clock on %s after %.0f s of debugger time" % (
            c.get("reward"), f.get("name"), c.get("spent") or 0)

    rows = [
        ["300 seconds for the whole graded set (`tests/judge.py` LIMIT, stated as the debugger's 300 seconds)",
         "`authoring/line-step-stop/variants/v2/steps.py`, a second engine written apart from the reference (plants every decision address of the stepping function)",
         "V2 used %.1f s (reward %s) and the reference %.1f s (reward %s) of debugger time for the whole set in the host trial; the exactly correct single-stepping `authoring/line-step-stop/variants/slow/steps.py`: %s; the half-way `authoring/line-step-stop/variants/half/steps.py`: %s" % (
             v2, v2_r, ref, ref_r, died(slow), died(half))],
        ["programs of up to 400 addresses (`tests/seal/forge.py` MAX_ADDRESSES)",
         "`tests/seal/forge.py` rejects any longer program before a session is built; `tests/seal/model.py` parses every graded image",
         "largest program over the %d frozen sessions and %d freshly generated ones: %d addresses" % (len(sessions), len(gen), most_addr)],
        ["loops of up to 700,000 iterations (`authoring/line-step-stop/make_heavy.py` draws heavy counts from 250,000 to 700,000)",
         "`tests/seal/model.py` executes every frozen session one instruction at a time",
         "largest value on any frozen tape: %d; largest on %d freshly generated tapes: %d" % (most_loop, len(gen), gen_loop)],
    ]
    json.dump({"rows": rows}, open(os.path.join(HERE, "timing_report.json"), "w"), indent=1)
    for r in rows:
        print(" | ".join(r))


if __name__ == "__main__":
    main()
