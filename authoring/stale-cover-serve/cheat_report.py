"""Grade every cheat, and say which layer stopped it rather than only that it scored 0.

A reward of 0 is the weakest possible evidence about a cheat: it is what a probe that never
fired scores, and what a forgery that stopped working after the first program scores. So this
asks a sharper question of each kind.

  readings    which enumerated case fails, and how much of a generated sample the reading
              moves. The case must be the one the trace names for it, or the set is not
              pinning the rule it claims to.
  shortcuts   how many programs the strategy matches at all, so a constant that happens to be
              right on most of them is visible as such rather than hidden behind the 0.
  the forgery which programs it reproduces. It has to reproduce every enumerated one - that is
              what makes it a forgery rather than a broken engine - and fail the generated
              population.
  the probes   what they found. Each runs the whole verifier and reports the lines it wrote
              into the sandbox work directory: the uid it ran as, what happened when it
              reached for the reward, the sealed answers and the model.

    python -u authoring/stale-cover-serve/cheat_report.py
"""
import pathlib
import random
import re
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import host_trial  # noqa: E402
import lab  # noqa: E402
import make_trace  # noqa: E402

CHEAT = lab.TASK / "cheat"
BLOCK = re.compile(r"cat > /app/rng/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF", re.S)

WANT = {
    "probe-privilege": ["uid 1002", "reward PermissionError"],
    "probe-answer-key": ["gt PermissionError", "model ModuleNotFoundError"],
    "probe-reward-later": ["spawned from "],
    "probe-plant-record": ["planted an empty record"],
    "probe-plant-then-die": ["planted, now leaving"],
}


def files_of(script):
    return {name: body for name, body in BLOCK.findall(script.read_text(encoding="utf-8"))}


def sample(n):
    gen = lab.gen()
    out = []
    per = max(1, n // len(gen.SMALL))
    for fam in gen.SMALL:
        for i in range(per):
            rng = random.Random("report|%s|%d" % (fam, i))
            out.append(("%s-%d" % (fam, i), "\n".join(gen.BUILD[fam](rng))))
    return out


def main():
    cases = lab.cases()
    model = lab.model()
    ref = lab.tree(lab.SOL)

    hand = [(n, "\n".join(cases.prog(n)) + "\n") for n in cases.ORDER]
    wild = [(n, t + "\n") for n, t in sample(90)]
    truth = {n: lab.run_text(ref, t) for n, t in hand}
    truth.update({n: model.trace(t) for n, t in wild})

    bad = 0
    rows = []
    for script in sorted(CHEAT.glob("cheat-*.sh")):
        name = script.stem[len("cheat-"):]
        if name.startswith("probe-"):
            # A probe runs in its own verifier below. Never in this process: two of them
            # kill their parent or exit it, which would take the report with them.
            continue
        files = files_of(script)
        if not files:
            rows.append((name, "no files written by the script", 0, 0))
            continue
        room = pathlib.Path(tempfile.mkdtemp(prefix="scs-cheat-"))
        try:
            for part, body in files.items():
                (room / part).write_text(body + "\n", encoding="utf-8", newline="\n")
            here = lab.tree(lab.SOL, files)
            fell = []
            for n, t in hand:
                try:
                    got = lab.run_text(here, t)
                except Exception:
                    got = None
                if got != truth[n]:
                    fell.append(n)
            moved = 0
            for n, t in wild:
                try:
                    got = lab.run_text(here, t)
                except Exception:
                    got = None
                if got != truth[n]:
                    moved += 1
        finally:
            shutil.rmtree(room, ignore_errors=True)
        rows.append((name, fell, moved, len(wild)))

    print("%-24s %5s %5s  %s" % ("cheat", "hand", "gen", "verdict"))
    for name, fell, moved, total in rows:
        if isinstance(fell, str):
            print("%-24s %s" % (name, fell))
            bad += 1
            continue
        note = ""
        if name in make_trace.READINGS:
            want = make_trace.READINGS[name][2]
            if want in fell:
                note = "caught by %s" % want
            else:
                note = "NOT CAUGHT by %s, which the trace names for it" % want
                bad += 1
        elif name == "forge-hand":
            if fell:
                note = "NOT a forgery: it fails %d enumerated programs" % len(fell)
                bad += 1
            elif moved == 0:
                note = "NOT a forgery: it also reproduces the generated population"
                bad += 1
            else:
                note = "reproduces all %d enumerated, fails %d of %d generated" \
                    % (len(hand), moved, total)
        else:
            note = "shortcut"
        if not fell and not moved:
            note += " - matches everything sampled"
            bad += 1
        print("%-24s %5d %5d  %s" % (name, len(fell), moved, note))

    print("")
    print("isolation probes, run through the whole verifier:")
    for name in sorted(n for n in WANT) + ["probe-garbage-record", "probe-kill-verifier"]:
        script = CHEAT / ("cheat-%s.sh" % name)
        if not script.is_file():
            print("   %-22s missing" % name)
            bad += 1
            continue
        reward, notes = host_trial.probe_run("cheat: " + name, script)
        said = " | ".join(notes.strip().splitlines()) if notes else "(wrote nothing)"
        ok = reward == 0 and all(bit in notes for bit in WANT.get(name, []))
        if not ok:
            bad += 1
        print("   %-22s reward=%d %-4s %s" % (name, reward, "ok" if ok else "BAD", said))

    print("")
    print("%d problem(s)" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
