"""Search for the worked example the brief prints, do not choose it.

A published example is evidence, and evidence that decides a load-bearing reading is an oracle.
This runs every candidate program under the reference and under every wrong reading, keeps the
ones that decide none of them, and prints the shortest ones together with the kinds of event
they show.
"""
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402

HAND = [
    ["take j1 b1:s1 r", "take j2 b1:s1 r", "show b1:s1", "take j3 b1:s1 w",
     "drop j1 b1:s1", "drop j2 b1:s1", "show b1:s1"],
    ["take j1 b1:s1 r", "take j2 b1:s2 w", "show b1:s1", "take j3 b1:s1 r",
     "drop j1 b1:s1", "show b1:s1", "end j2"],
    ["take j1 b1:s4 w", "take j2 b1:s4 r", "show b1:s4", "drop j1 b1:s4", "show b1:s4"],
    ["take j1 b2:s1 r", "take j1 b2:s1 w", "show b2:s1", "drop j1 b2:s1", "end j1"],
    ["take j1 b1:s1 w", "take j2 b1:s2 r", "take j3 b1:s1 r", "drop j1 b1:s1",
     "show b1:s1", "end j2"],
]


def policy(files):
    room = pathlib.Path(tempfile.mkdtemp(prefix="ccl-pick-"))
    for part in lab.PARTS:
        shutil.copy(lab.TASK / "solution" / part, room / part)
    for part, src in files.items():
        (room / part).write_text(src, encoding="utf-8", newline="\n")
    return room


def main():
    alts = []
    for build in emit.READINGS:
        name, _comment, files = build()
        alts.append((name, lab.tree(policy(files))))
    ref = lab.tree(lab.TASK / "solution")

    pool = [("hand-%d" % i, body) for i, body in enumerate(HAND)]
    for round_ in range(1, 12):
        for fam, name, body in gen.programs("pick-%d" % round_, 2):
            if fam not in ("big", "busy", "lines") and len(body) <= 14:
                pool.append((name, body))

    good = []
    for name, body in pool:
        try:
            want = lab.run(ref, body)
        except Exception:
            continue
        if not want:
            continue
        decided = []
        for alt_name, alt in alts:
            try:
                got = lab.run(alt, body)
            except Exception:
                decided.append(alt_name)
                break
            if got != want:
                decided.append(alt_name)
                break
        if decided:
            continue
        kinds = {line.split()[0] for line in want}
        good.append((len(body), -len(kinds), name, body, want, sorted(kinds)))
    good.sort()
    print("%d of %d candidates decide no reading" % (len(good), len(pool)))
    for size, negk, name, body, want, kinds in good[:6]:
        print("--- %s  %d lines, events %s" % (name, size, " ".join(kinds)))
        for line in body:
            print("    | %s" % line)
        for line in want:
            print("    > %s" % line)


if __name__ == "__main__":
    main()
