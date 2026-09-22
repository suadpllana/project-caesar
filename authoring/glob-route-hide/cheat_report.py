#!/usr/bin/env python3
"""What catches each cheat, and how much of the population it moves. Never ships.

A zero reward says nothing about why. This asserts the layer:

  reading    the enumerated case the reading is named for fails it, in process, and the
             fraction of generated programs (one seed, the small families) it gets wrong is
             printed - a reading that moves almost nothing is one the population is not shaped
             for, however well a hand case pins it;
  shortcut   how many enumerated cases and generated programs it matches;
  forgery    it passes every enumerated case and still fails the generated population;
  slow       it matches every enumerated case exactly - so only the clock can stop it;
  probe      reported from the real trial below, by its probe log.

With --trials every cheat also goes through host_trial.py (the verifier's test.sh, verbatim,
as root) and must score 0.

    python3 -u authoring/glob-route-hide/cheat_report.py [--trials]
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

SEED = "report-seed"


def files_of(script):
    """Parse a cheat script back into {published path: text}."""
    out, cur, buf = {}, None, []
    for ln in script.read_text(encoding="utf-8").splitlines():
        if cur is None and ln.startswith("cat > ") and ln.endswith("<<'PYEOF'"):
            cur = ln[len("cat > "):-len(" <<'PYEOF'")]
            buf = []
        elif cur is not None and ln == "PYEOF":
            out[cur] = "\n".join(buf) + "\n"
            cur = None
        elif cur is not None:
            buf.append(ln)
    return out


def tree_for(script):
    got = files_of(script)
    five = {Path(p).name: t for p, t in got.items() if p.startswith("/app/fe/")}
    return lab.tree(files=five)


def main():
    trials = "--trials" in sys.argv[1:]
    emit.main()
    cases, gen, model = lab.sealed()
    hand = [(n, cases.prog(n)) for n in cases.ORDER]
    truth = {n: model.expect(lines) for n, lines in hand}
    small = [(fam, name, lines) for fam, name, lines in gen.programs(SEED, 40)
             if fam not in ("tree", "mesh")]
    want = {name: model.expect(lines) for _f, name, lines in small}

    rows, bad = [], 0
    for name in emit.MADE:
        kind = emit.KIND[name]
        script = lab.TASK / "cheat" / ("cheat-%s.sh" % name)
        if kind in ("probe",):
            rows.append((name, kind, "see trial"))
            continue
        here = tree_for(script)
        failed = [n for n, lines in hand
                  if lab.run_text(here, "\n".join(lines) + "\n") != truth[n]]
        if kind == "slow":
            note = "matches %d/%d enumerated exactly" % (len(hand) - len(failed), len(hand))
            if failed:
                note += " - NOT EXACT: %s" % failed[:3]
                bad += 1
            rows.append((name, kind, note))
            lab.drop(here)
            continue
        moved = sum(1 for _f, n, lines in small
                    if lab.run_text(here, "\n".join(lines) + "\n") != want[n])
        frac = "%d/%d generated wrong (%.0f%%)" % (moved, len(small), 100.0 * moved / len(small))
        if kind == "reading":
            named = emit.CATCH.get(name)
            ok = named in failed
            note = "caught by %s%s; %d enumerated fail; %s" % (
                named, "" if ok else " - NOT CAUGHT BY ITS CASE", len(failed), frac)
            bad += 0 if ok else 1
        elif kind == "forgery":
            ok = not failed and moved > 0
            note = "passes %d/%d enumerated, %s%s" % (len(hand) - len(failed), len(hand), frac,
                                                      "" if ok else " - FORGERY NOT DEMONSTRATED")
            bad += 0 if ok else 1
        else:
            note = "matches %d/%d enumerated, %s" % (len(hand) - len(failed), len(hand), frac)
            if not failed and not moved:
                note += " - SHORTCUT PASSES"
                bad += 1
        rows.append((name, kind, note))
        lab.drop(here)

    for name, kind, note in rows:
        print("%-24s %-8s %s" % (name, kind, note), flush=True)

    if trials:
        print("\n-- host trials (tests/test.sh verbatim) --", flush=True)
        for name in emit.MADE:
            script = lab.TASK / "cheat" / ("cheat-%s.sh" % name)
            r = subprocess.run([sys.executable, "-u", str(HERE / "host_trial.py"), "--cheat",
                                str(script)], capture_output=True, text=True)
            out = r.stdout.strip().splitlines()
            print("\n".join(out[-8:]), flush=True)
            if r.returncode != 0:
                bad += 1
    print("\n%d problems" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
