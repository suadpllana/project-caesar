"""Score the dumbest strategies (docs/INSTRUCTION-CONTRACT.md, Shortcuts) by fraction matched.

All-or-nothing grading turns a strategy that matches 90% of sessions into a 0 and hides that
the data barely exercises the rule, so this records the fraction of sessions each one prints
exactly, over the small frozen sessions and a fresh generated population, next to the reward
its cheat script scored in the host trial (cheat_report.json). Writes shortcut_report.json.
"""
import json
import os
import random
import re
import shutil
import tempfile

from lab import HERE, SEAL, TASK, forge
import bench
import fastbench

STRATEGIES = [
    ("cut-shipped", "the shipped tree unchanged (nop)"),
    ("cut-constant", "constant: every command prints exit and every breakpoint resolves to nothing"),
    ("cut-first-location", "positional: every breakpoint takes only its first statement row"),
    ("cut-one-instruction", "positional: every step, next and finish moves exactly one instruction"),
    ("cut-innermost-only", "positional: a stop prints only the innermost real frame"),
    ("cut-replay-example", "the worked example's output replayed for every session"),
    ("read-inrow-call-unplanted", "the previous revision of a correct engine (V2 before its in-row call fix)"),
]


def extract(script):
    text = open(script).read()
    d = tempfile.mkdtemp(prefix="lss-cut-")
    for name, body in re.findall(r"cat > /app/dbg/(\w+\.py) <<'LSS_EOF'\n(.*?)\nLSS_EOF", text, re.S):
        with open(os.path.join(d, name), "w") as f:
            f.write(body + "\n")
    return d


def main():
    fixed = json.load(open(os.path.join(SEAL, "gt.json")))
    small = [s for g in ("samples", "cases", "fences") for s in fixed[g] if s.get("recheck")]
    rng = random.Random(99)
    nonce = [forge.session(f, rng) for f in sorted(forge.FAMILIES) for _ in range(34)]
    pop = small + nonce
    trials = json.load(open(os.path.join(HERE, "cheat_report.json")))
    out = {}
    for name, what in STRATEGIES:
        d = extract(os.path.join(TASK, "cheat", "cheat-%s.sh" % name))
        res = fastbench.run(d, pop)
        shutil.rmtree(d)
        ok = len(pop) - len(bench.compare(pop, res))
        reward = trials.get(name[len("cheat-"):] if name.startswith("cheat-") else name, {}).get("reward")
        caught = (trials.get(name, {}).get("failed") or {}).get("name")
        out[name] = {"what": what, "matched": ok, "of": len(pop),
                     "result": "reward %s in the host trial (first failing session: %s); matches %d of %d sessions exactly (%.1f%%)"
                               % (reward, caught, ok, len(pop), 100.0 * ok / len(pop))}
        print("%-28s %s" % (name, out[name]["result"]), flush=True)
    json.dump(out, open(os.path.join(HERE, "shortcut_report.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
