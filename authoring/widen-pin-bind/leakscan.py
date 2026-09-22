"""Try to reconstruct a graded answer from the shipped tree with no reasoning at all.

The leak audit in docs/DIFFICULTY.md is a procedure rather than a feeling: write down the
answer a stage is supposed to produce, then try to produce it from the files the agent can see
by joining, sorting or matching. This does the mechanical half - no correct output line of any
shipped program appears anywhere in the tree, nothing under environment/ names the verifier's
own material, and no shipped file carries a derived quantity of its own.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

# The verifier's own material, by the names it goes under. `expected` is deliberately not
# here: it is the shipped code's word for the kind a call is asked for, which the brief states.
BLOCK = ("gt.json", "model.expect", "cases.order", "/tests", "seal/", "worker_out",
         "reward.txt", "nonce", "pristine")


def main():
    files = [p for p in lab.SRC.rglob("*") if p.is_file()]
    text = {p: p.read_text(encoding="utf-8", errors="replace") for p in files}
    bad = 0

    for prog in sorted((lab.SRC / "progs").glob("*.txt")):
        want = lab.run_text(lab.SOL, prog.read_text(encoding="utf-8"))
        for line in want:
            if len(line.split()) < 2:
                continue
            for p, body in text.items():
                if p == prog:
                    continue
                if line in body:
                    print("LEAK %s carries %r, an answer line of %s" % (p.name, line, prog.name))
                    bad += 1
    print("checked %d programs against %d shipped files" % (
        len(list((lab.SRC / "progs").glob("*.txt"))), len(files)))

    for p, body in text.items():
        for word in BLOCK:
            if word in body.lower() and p.suffix == ".py":
                print("LEAK %s mentions %r" % (p.name, word))
                bad += 1

    # a derived quantity stored on a shipped record: the tree may hold kinds, edges, entries,
    # values and expressions, and nothing that is computed from them
    for p, body in text.items():
        if p.suffix != ".txt":
            continue
        for row in body.splitlines():
            head = row.split(" ", 1)[0] if row.strip() else ""
            if head and head not in ("kind", "rise", "entry", "open", "val", "ask"):
                print("LEAK %s has a line starting %r" % (p.name, head))
                bad += 1
    print("findings: %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
