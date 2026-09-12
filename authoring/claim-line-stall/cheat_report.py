"""Which layer catches each cheat - not merely that it scored 0.

A cheat that scores 0 for a reason the author did not intend is a cheat that proves nothing,
and a layer report is the only thing that notices. The semantic cheats and the forgery are run
here, in process, against the enumerated cases and a nonce population. The probes are not: they
fork, exit and write outside the tree, so the container run is the only place they mean
anything, and they are listed as such.
"""
import pathlib
import re
import sys
import traceback

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "claim-line-stall"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402

MODS = ("ops", "hold", "hold.name", "hold.say", "hold.book", "hold.line", "hold.lift",
        "hold.knot", "hold.turn", "hold.act")
PARTS = ("book.py", "line.py", "lift.py", "knot.py", "turn.py", "act.py")
BLOCK = re.compile(r"cat > /app/hold/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF", re.S)


def unpack(sh, room):
    room.mkdir(parents=True, exist_ok=True)
    got = set()
    for name, body in BLOCK.findall(sh.read_text(encoding="utf-8")):
        (room / name).write_text(body + "\n", encoding="utf-8", newline="\n")
        got.add(name)
    if got != set(PARTS):
        sys.exit("%s writes %s" % (sh.name, sorted(got)))
    return room


def load(over):
    here = lab.stage(over)
    sys.path.insert(0, str(here))
    for one in MODS:
        sys.modules.pop(one, None)
    import ops as mod
    from hold import book as bk
    sys.path.remove(str(here))
    return mod, bk


def run(pair, lines):
    mod, bk = pair
    try:
        h = bk.Hold()
        for line in lines:
            mod.ex(h, tuple(line.split()))
        return h.out
    except Exception:
        return ["raised: " + traceback.format_exc(limit=1).strip().splitlines()[-1]]


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    hand = [(n, cases.ops(n)) for n in cases.ORDER]
    pop = [(n, l) for _f, n, l in gen.programs("cheatreport", per)
           if not n.startswith(("wide", "tall"))]
    ref = load(str(TASK / "solution"))
    want_hand = {n: run(ref, l) for n, l in hand}
    want_pop = {n: run(ref, l) for n, l in pop}

    room = pathlib.Path(HERE / ".unpacked")
    bad = []
    for sh in sorted((TASK / "cheat").glob("*.sh")):
        tag = sh.stem.replace("cheat-", "")
        if tag.startswith("probe-"):
            print("%-22s %s" % (tag, "container only - the isolation run is its layer"))
            continue
        if tag.startswith("slow-"):
            print("%-22s %s" % (tag, "exactly correct - the execution limit is its layer"))
            continue
        pair = load(str(unpack(sh, room / tag)))
        caught = [n for n, l in hand if run(pair, l) != want_hand[n]]
        moved = [n for n, l in pop if run(pair, l) != want_pop[n]]
        if tag == "forge-from-truth":
            where = "every enumerated case passes, %d of %d nonce programs fail" % (
                len(moved), len(pop))
            if caught:
                where = "BROKEN: it fails %d enumerated cases too" % len(caught)
                bad.append(tag)
            elif not moved:
                where = "NOT CAUGHT"
                bad.append(tag)
        elif caught:
            where = "%s (+%d more, %d of %d nonce)" % (caught[0], len(caught) - 1,
                                                       len(moved), len(pop))
        else:
            where = "NOT CAUGHT by any enumerated case"
            bad.append(tag)
        print("%-22s %s" % (tag, where))
    print("%s" % ("all cheats are caught by a named layer" if not bad
                  else "UNCAUGHT: %s" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
