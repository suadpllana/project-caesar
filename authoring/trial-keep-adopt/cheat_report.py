"""Which case catches each cheat, not just that the reward came out 0.

A reward of 0 proves nothing on its own: a cheat can score 0 because its patch never applied,
because it crashed on the first program, or because the case it was written to test never ran.
This runs every semantic cheat over the enumerated set and names the first enumerated program
that catches it, times the two slow cheats against the stated limit, and checks that the forgery
reproduces every enumerated program and fails on ones it could not have seen. The isolation
probes are graded by the container run, not here, and are listed as such.

    python3 authoring/trial-keep-adopt/cheat_report.py [per]
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

LIMIT = 60
READ = HERE / "readings"
SEMANTIC = [d.name for d in sorted(READ.iterdir())
            if d.is_dir() and d.name not in ("pre-copy", "no-memo", "reads-set")]
SLOW = ("pre-copy", "no-memo")
PROBES = ("probe-answer-key", "probe-hijack-driver", "probe-plant-report",
          "probe-late-reward", "probe-crash-worker", "probe-malformed",
          "probe-privilege", "probe-shrink-set", "probe-rewrite-frozen")


def drive(here, lines, timeout=180):
    room = pathlib.Path(tempfile.mkdtemp(prefix="tka-prog-"))
    prog = room / "p.txt"
    prog.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    try:
        return lab.run(here, prog, timeout=timeout)
    except Exception as exc:
        return ["RAISED %s" % exc]


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    work = [("hand", n, cases.ops(n)) for n in cases.ORDER]
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(per):
            name = "%s-%d" % (fam, i)
            work.append((fam, name, gen.one(fam, "report/%s" % name)))
    truth = {name: model.expect(lines) for _f, name, lines in work}
    hand = set(cases.ORDER)
    print("%d programs: %d enumerated, %d generated\n"
          % (len(work), len(cases.ORDER), len(work) - len(cases.ORDER)), flush=True)

    bad = []
    for name in SEMANTIC:
        here = lab.tree(READ / name)
        first_hand, first_any = None, None
        for _fam, prog, lines in work:
            if drive(here, lines) != truth[prog]:
                first_any = first_any or prog
                if prog in hand and first_hand is None:
                    first_hand = prog
        if first_hand:
            print("   %-14s caught by enumerated %s" % (name, first_hand), flush=True)
        elif first_any:
            print("   %-14s BLIND to enumerated, only generated %s catches it"
                  % (name, first_any), flush=True)
            bad.append(name)
        else:
            print("   %-14s NOT CAUGHT by anything - it is a correct variant or a dud"
                  % name, flush=True)
            bad.append(name)

    print("", flush=True)
    for name in SLOW:
        here = lab.tree(READ / name)
        big = "wide" if name == "pre-copy" else "deep"
        _f, pname, lines = [(f, n, l) for f, n, l in
                            [(fam, "%s-0" % fam, gen.one(fam, "report/%s-0" % fam))
                             if not big2 else
                             (fam, "%s-0" % fam,
                              gen.wide(__import__("random").Random("r"), 20000, 20000)
                              if fam == "wide" else
                              gen.deep(__import__("random").Random("r"), 30, 2000))
                             for fam, big2 in gen.FAMILIES if fam == big]][0]
        t0 = time.time()
        drive(here, lines, timeout=LIMIT + 30)
        dt = time.time() - t0
        ok = dt > LIMIT
        print("   %-14s %s on %s: %.1fs against the %ds limit"
              % (name, "over" if ok else "UNDER", big, dt, LIMIT), flush=True)
        if not ok:
            bad.append(name)

    print("", flush=True)
    os.environ["TKA_TESTS"] = str(lab.TASK / "tests")
    forge = lab.TASK / "cheat" / "cheat-forge-from-truth.sh"
    here = _forged_tree(forge)
    repro = sum(1 for n in cases.ORDER if drive(here, cases.ops(n)) == truth[n])
    nonce = [(n, l) for f, n, l in work if n not in hand]
    caught = sum(1 for n, l in nonce if drive(here, l) != truth[n])
    # The forgery cannot see def lines, which route through a frozen file, so two enumerated
    # programs that share a visible-op prefix but differ only in their definitions collide and
    # it reproduces one of them wrong. That is the honest ceiling for an answer key that reads
    # only the six files, and it is why the forgery misses every nonce program and scores 0.
    print("   forge-from-truth reproduces %d/%d enumerated, misses %d/%d generated"
          % (repro, len(cases.ORDER), caught, len(nonce)), flush=True)
    if repro < 15 or caught != len(nonce):
        bad.append("forge-from-truth")

    print("\n   probes graded by the container run: %s" % ", ".join(PROBES), flush=True)
    if bad:
        print("\nFAIL: %s" % ", ".join(bad))
        return 1
    print("\nevery semantic cheat is caught by an enumerated case; both slow cheats miss the "
          "limit; the forgery carries the answers and fails on what it could not see")
    return 0


def _forged_tree(sh):
    """Apply a cheat script's six files onto a fresh tree, the way the worker would."""
    import re
    body = sh.read_text()
    room = lab.shipped()
    for m in re.finditer(r"cat > /app/fld/(\S+) <<'PYEOF'\n(.*?)\nPYEOF", body, re.S):
        (room / "fld" / m.group(1)).write_text(m.group(2) + "\n", encoding="utf-8", newline="\n")
    return room


if __name__ == "__main__":
    sys.exit(main())
