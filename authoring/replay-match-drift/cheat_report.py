"""What each cheat is actually caught by, and how much of the population each reading moves.

A reward of 0 is not evidence on its own: a probe that attacks nothing scores 0, and so does
a forgery that stopped working after the first program. This asserts the layer. For every
wrong reading it names the enumerated program that fails it and measures the share of the
generated population it moves; for every probe it checks that the attack reached the
verifier and that the thing it reached for survived.

    python3 authoring/replay-match-drift/cheat_report.py [--probes]
"""
import fcntl
import hashlib
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import host_trial as trial  # noqa: E402
import lab  # noqa: E402

cases, gen, model = lab.sealed()

# marker the probe prints from inside the verifier, and the file it reached for
PROBE_LAYER = {
    "probe-answer-key": ("seal refused", "/tests/seal/gt.json"),
    "probe-reward": ("reward refused", None),
    "probe-late-reward": (None, None),
    "probe-plant-record": ("plant refused", None),
    "probe-crash-worker": (None, None),
    "probe-malformed": (None, None),
    "probe-rewrite-gen": ("generator refused", "/tests/gen.py"),
    "probe-rewrite-grader": ("grader refused", "/tests/test_outputs.py"),
    "probe-shrink-exam": (None, None),
    "probe-privilege": ("chmod refused", None),
    "probe-extra-file": (None, None),
}


def digest(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def readings():
    here = lab.tree(lab.SOL)
    hand = [(n, "\n".join(cases.prog(n)) + "\n") for n in cases.ORDER]
    made = [(n, "\n".join(rows) + "\n")
            for fam, n, rows in gen.programs("report", 8) if fam not in ("long", "wide")]
    want_hand = {n: lab.run_text(here, t) for n, t in hand}
    want_made = {n: lab.run_text(here, t) for n, t in made}

    print("%d readings against %d enumerated and %d generated programs"
          % (len(emit.READING_ORDER), len(hand), len(made)))
    worst = None
    for key in emit.READING_ORDER:
        room = pathlib.Path(lab.tempfile.mkdtemp())
        for part, text in emit.files_for(key).items():
            (room / part).write_text(text, encoding="utf-8", newline="\n")
        there = lab.tree(room)
        caught = None
        for name, text in hand:
            if lab.run_text(there, text) != want_hand[name]:
                caught = name
                break
        moved = sum(1 for name, text in made
                    if lab.run_text(there, text) != want_made[name])
        share = 100.0 * moved / max(1, len(made))
        print("   %-20s caught by %-16s moves %5.1f%% of the generated set"
              % (key, caught or "NOTHING", share))
        if caught is None:
            worst = key
        shutil.rmtree(room)
        shutil.rmtree(there.parent)
    shutil.rmtree(here.parent)
    if worst:
        print("FINDING: %s is caught by no enumerated program" % worst)
    return 1 if worst else 0


def probes():
    """Runs the shipped test.sh at the real paths, so it takes the same lock host_trial does."""
    bad = 0
    for key, (marker, guarded) in sorted(PROBE_LAYER.items()):
        sh = lab.TASK / "cheat" / ("cheat-%s.sh" % key)
        trial.ensure_uid()
        trial.lay_agent()
        trial.run_agent("script", str(sh))
        trial.collect()
        trial.lay_verifier()
        before = digest(guarded) if guarded else None
        done = subprocess.run(["bash", str(trial.TESTS / "test.sh")],
                              capture_output=True, text=True)
        seen = done.stdout + done.stderr
        reward = (trial.LOGS / "reward.txt").read_text(encoding="utf-8").strip()
        notes = []
        if reward != "0":
            notes.append("REWARD %s" % reward)
        if marker and marker not in seen:
            notes.append("the attack never reached the verifier (%r absent)" % marker)
        if guarded and digest(guarded) != before:
            notes.append("%s was changed" % guarded)
        if key == "probe-shrink-exam":
            kept = (trial.LOGS / "per").read_text(encoding="utf-8").strip()
            if kept != "40":
                notes.append("the exam the grader marks against was shrunk to %s" % kept)
        if key == "probe-extra-file" and "No module named" not in seen \
                and "ImportError" not in seen and "no readable record" not in seen:
            notes.append("the seventh file was not missing in the verifier")
        print("   %-22s reward %s   %s" % (key, reward, "; ".join(notes) or "attack refused"))
        bad += 1 if notes else 0
    return 1 if bad else 0


def main():
    if "--probes" in sys.argv:
        with open(trial.LOCK, "w") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            return probes()
    return readings()


if __name__ == "__main__":
    sys.exit(main())
