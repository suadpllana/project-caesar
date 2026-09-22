"""What catches each cheat, not just that its reward was 0.

A zero on its own does not distinguish a probe the verifier caught from one whose patch never
fired. This runs every cheat in the host emulation and names the layer: which enumerated case
it fails first, and how much of a generated sample it moves. It then asserts the two things a
reward cannot tell you - that each wrong reading is caught by the enumerated case named after
it, and that the answer-key forgery really does reproduce the enumerated programs it claims to,
rather than scoring 0 because it silently stopped working.

The isolation probes are judged in the container by tools/docker_trial.py, since nothing on the
host has a privilege drop or a root-owned reward; here they are only checked to be inert, which
is what a probe that does no work should be.

    python3 cheat_report.py          (run from tasks/page-bound-cut, as forgecheck does)
"""
import pathlib
import random
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, model = lab.sealed()
CHEATS = lab.TASK / "cheat"
BLOCK = re.compile(r"cat > /app/pg/([A-Za-z0-9_]+\.py) <<'PYEOF'\n(.*?)\nPYEOF", re.S)


def files_of(script):
    return {m.group(1): m.group(2) + "\n" for m in BLOCK.finditer(script.read_text())}


def sample(n=40):
    out = []
    rng = random.Random(5150)
    for row in gen.FAMILIES:
        for k in range(max(1, n // len(gen.FAMILIES))):
            out.append(("%s-%d" % (row[0], k), gen.build(row, 70000 + rng.randrange(999))))
    return out


def main():
    hand = [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]
    made = sample()
    bad = []
    rows = []
    probes = []
    for script in sorted(CHEATS.glob("cheat-*.sh")):
        tag = script.stem[len("cheat-"):]
        if tag.startswith("probe-"):
            # A probe attacks the verifier rather than the problem, and one of them exits the
            # interpreter on purpose. Nothing on this host has a privilege drop or a root-owned
            # reward to attack, so they are judged in the container by tools/docker_trial.py.
            probes.append(tag)
            continue
        files = files_of(script)
        room = lab.spill({}) if files else None
        if files:
            # a cheat writes over the shipped tree, so start from the shipped policy
            for part in lab.PARTS:
                (room / part).write_text((lab.SRC / "pg" / part).read_text(encoding="utf-8"),
                                         encoding="utf-8", newline="\n")
            for name, body in files.items():
                (room / name).write_text(body, encoding="utf-8", newline="\n")
            here = lab.tree(room)
        else:
            here = lab.tree(lab.SRC / "pg")
        first = None
        passed_hand = 0
        own = None
        for name, body in hand:
            ok = lab.run_text(here, body) == model.trace(body)
            if ok:
                passed_hand += 1
            elif first is None:
                first = name
            if name == tag:
                own = ok
        moved = sum(1 for _n, b in made if lab.run_text(here, b) != model.trace(b))
        rows.append((tag, first, passed_hand, moved, own))
        if first is None and moved == 0:
            bad.append("%s: nothing catches it - it would score 1" % tag)
        # a wrong reading has to be caught by the case named after it, whichever case the
        # alphabetical sweep happens to reach first
        if tag in set(cases.ORDER) and own is not False:
            bad.append("%s: the case named for it does not fail it" % tag)
    forge = dict((t, (f, p, m)) for t, f, p, m, _o in rows).get("forge-hand")
    if forge is None:
        bad.append("no forgery probe in cheat/")
    else:
        first, passed, moved = forge
        if passed != len(hand):
            bad.append("forge-hand reproduces only %d of %d enumerated programs, so its zero "
                       "says nothing about the population" % (passed, len(hand)))
        if moved == 0:
            bad.append("forge-hand is not separated by the generated population")
    for tag, first, passed, moved, own in rows:
        print("  %-20s own case %-5s first failure %-14s enumerated %2d/%d  generated moved %2d/%d"
              % (tag, {True: "PASS", False: "fails", None: "-"}[own], first or "none",
                 passed, len(hand), moved, len(made)))
    if bad:
        print("\n".join("  FAIL %s" % b for b in bad))
        print("cheat report: %d finding(s)" % len(bad))
        return 1
    print("  isolation probes judged in the container, not here: %s" % ", ".join(probes))
    print("cheat report: %d cheats read here and %d probes left to the container, every one "
          "caught, and the forgery reproduces all %d enumerated programs while failing the "
          "generated sample" % (len(rows), len(probes), len(hand)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
