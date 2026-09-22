#!/usr/bin/env python3
"""The probes that carry correct work, run with the isolation they target taken away. Never ships.

A probe that scores 0 because it attacks nothing looks exactly like one the isolation stopped.
Three probes carry a correct resolver where the verifier never runs it: the sealed model read
out of /tests/seal, a resolver in a sixth file beside the five, and one pasted into the driver.
Each is run here with its piece of isolation missing - as root, so the seal reads, and on a tree
holding every file the script wrote, so the sixth file and the driver are the ones used - and
must then print the right lines for every hand program and for one program of each large shape.
If one of them does not, its zero in the trial proves nothing.

Needs the /tests/seal that host_trial.py leaves on this host after any run.

    python3 -u authoring/glob-route-hide/probe_controls.py
"""
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
from cheat_report import files_of  # noqa: E402

PROBES = ("probe-answer-key", "probe-uncollected-file", "probe-engine-in-driver")


def unguarded(script):
    """The shipped tree with every file the script wrote, driver and sixth files included."""
    here = lab.tree()
    for path, text in files_of(script).items():
        assert path.startswith("/app/"), path
        dest = here / path[len("/app/"):]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8", newline="\n")
    return here


def main():
    if not Path("/tests/seal/gt.json").is_file():
        raise SystemExit("no /tests/seal on this host: run host_trial.py once first")
    cases, gen, model = lab.sealed()
    progs = [("hand", n, cases.prog(n)) for n in cases.ORDER]
    progs += [(fam, name, lines) for fam, name, lines in gen.programs("probe-controls", 1)
              if fam in ("tree", "mesh") and name.endswith("-00")]
    assert sum(1 for fam, _n, _l in progs if fam != "hand") == 2
    bad = 0
    for probe in PROBES:
        here = unguarded(lab.TASK / "cheat" / ("cheat-%s.sh" % probe))
        right, slowest = {"hand": 0, "large": 0}, 0.0
        for fam, _name, lines in progs:
            t0 = time.time()
            got = lab.run_shell(here, "\n".join(lines) + "\n", timeout=120)
            slowest = max(slowest, time.time() - t0)
            if got == model.expect(lines):
                right["hand" if fam == "hand" else "large"] += 1
        lab.drop(here)
        ok = right["hand"] == len(cases.ORDER) and right["large"] == 2
        bad += 0 if ok else 1
        print("%-24s unguarded: %d/%d hand, %d/2 large right, slowest program %.1fs%s" % (
            probe, right["hand"], len(cases.ORDER), right["large"], slowest,
            "" if ok else " - THE ATTACK DOES NOT WORK, SO ITS ZERO PROVES NOTHING"), flush=True)
    print("%d problems" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
