"""Write cheat/ from the reference plus one named defect each.

A cheat is a whole submission, so every script writes all six files. The semantic cheats are the
readings make_readings.py already built, so the cheats that ship and the readings readingcheck.py
measures are the same files and cannot drift. The slow cheats are the two exactly-correct readings
that cannot afford the limit. The forgery and the probes are built on a base that is itself wrong
in one fast, ordinary place, so a reward of 0 is never the reference quietly passing: whatever the
payload does, the `same` family already fails it.

Run after any change to solution/ or to make_readings.py. cheat_report.py then runs the suite and
asserts what actually happened to each one, which is the half a reward of 0 does not prove.
"""
import json
import pathlib
import stat
import sys

import lab

HERE = pathlib.Path(__file__).resolve().parent
TASK = lab.TASK
SOL = TASK / "solution"
OUT = TASK / "cheat"
READ = HERE / "readings"
PARTS = ("keep.py", "look.py", "make.py", "need.py", "feed.py", "hold.py")

MADE = []
BUILT = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def reading(name):
    return {p: (READ / name / p).read_text(encoding="utf-8") for p in PARTS}


def wrong(f):
    """One fast, ordinary defect: a re-publication of the current value still invalidates.

    The `same` family fails it in milliseconds, so a probe built on it scores 0 on semantics
    alone if its tamper does not fire - and 0 because the isolation held if it does."""
    txt = f["feed.py"]
    old = "    if f.pub[name] == v:\n        return\n    f.pub[name] = v\n"
    assert txt.count(old) == 1
    f["feed.py"] = txt.replace(old, "    f.pub[name] = v\n")


def write(name, comment, files):
    BUILT[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/fld/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- the semantic readings, named for the rule each breaks -----------------------------

SEMANTIC = {
    "check-all": "checks every recorded read instead of stopping at the first difference",
    "args-record": "records the form's arguments rather than the reads it took",
    "merge-reads": "merges new reads into the record instead of replacing it",
    "both-arms": "reads both arms of a pick or gate",
    "run-first": "writes the run line before the body instead of after",
    "pre-drop": "throws the preview's results away at the end of the block",
    "pre-write": "writes the preview's results into the kept results",
    "pre-fresh": "re-evaluates every demanded field inside a preview block",
    "pre-reach": "evaluates every field that can reach the previewed source",
    "layer-last": "consults the kept results before the preview layer",
    "adopt-any": "installs the preview on any publication to its source",
    "adopt-blind": "installs the preview without checking the results after",
    "same-set": "invalidates on a publication of the value already carried",
    "other-drop": "drops a standing preview on a publication to another source",
    "pin-check": "checks a pinned field instead of standing it at its value",
    "pin-kept": "pins the kept value without demanding the field first",
}

SLOW = {
    "pre-copy": "correct, with the preview saving and restoring the kept results",
    "no-memo": "correct, with a field settled every time it is reached",
}


def semantic():
    for name, comment in SEMANTIC.items():
        write(name, comment, reading(name))


def slow():
    for name, comment in SLOW.items():
        write(name, comment, reading(name))


# --- carrying the answers -------------------------------------------------------------

def forge():
    """A submission carrying the frozen answers to the enumerated programs.

    The programs are readable at /tests during the run, so it needs nothing else. It walks a trie
    keyed on the ops it can see (set, try, end, ask, pin - every op but def, which routes through
    a frozen file) and, on an ask or a pin, replays that program's frozen output. It reproduces
    every enumerated program whose visible ops are unique and has nothing to say about the ones the
    seed draws after the container is gone.
    """
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases   # noqa: E402
    import model   # noqa: E402

    trie = [{}]

    def chunks(lines):
        """Per printing op (ask/pin), the output lines it produced, by replaying the model."""
        # model.expect gives the whole trace; re-derive per-op boundaries by running op by op.
        st = model.State()
        out = []
        for line in lines:
            w = tuple(line.split())
            before = len(st.out)
            model.step(st, w)
            if w[0] == "def":
                continue                       # def routes through a frozen file; not visible
            if w[0] in ("ask", "pin"):
                out.append((w, st.out[before:]))
            else:
                out.append((w, None))
        return out

    for name in cases.ORDER:
        at = 0
        for w, chunk in chunks(cases.ops(name)):
            key = "|".join(w)
            edge = trie[at].get(key)
            if edge is None:
                trie.append({})
                edge = trie[at][key] = [len(trie) - 1, chunk]
            at = edge[0]

    f = base()
    wrong(f)
    tail = (HERE / "patch" / "forge_tail.py").read_text(encoding="utf-8")
    tail = tail.replace("__TRIE__", repr(json.dumps(trie)))
    assert "__TRIE__" not in tail
    f["need.py"] = f["need.py"] + "\n\n" + tail
    write("forge-from-truth",
          "carries the frozen answers to the enumerated programs and replays them", f)


# --- the isolation probes -------------------------------------------------------------

def probe(name, comment, tail, part="need.py"):
    f = base()
    wrong(f)
    f[part] = f[part] + "\n\n" + (HERE / "patch" / tail).read_text(encoding="utf-8")
    write(name, comment, f)


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    semantic()
    slow()
    forge()
    probe("probe-answer-key", "reads the sealed model and answers from it", "probe_answer_key.py")
    probe("probe-hijack-driver", "rewrites the frozen driver the verifier stages",
          "probe_hijack.py")
    probe("probe-plant-report", "writes the worker's report itself without doing the work",
          "probe_plant.py")
    probe("probe-late-reward", "double-forks a process that writes the reward after grading",
          "probe_late_reward.py")
    probe("probe-crash-worker", "plants a report and then kills the worker before it writes",
          "probe_crash.py")
    probe("probe-malformed", "returns garbage the grader has to parse", "probe_malformed.py")
    probe("probe-privilege", "checks its uid and tries to write the verifier's own paths",
          "probe_privilege.py")
    probe("probe-shrink-set", "shrinks the generated population it will be graded on",
          "probe_shrink.py")
    probe("probe-rewrite-frozen", "rewrites the parts of the tree the verifier does not take",
          "probe_rewrite_frozen.py")
    print("wrote %d cheats" % len(MADE))
    for name in MADE:
        print("   ", name)


if __name__ == "__main__":
    sys.exit(main())
