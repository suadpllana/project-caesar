#!/usr/bin/env python3
"""Search the sample documents for the frame the brief should print in full. Never ships.

The brief has to quote one correct line or a formatting slip fails every program for a reason
that is not the task - and that line is an oracle for whatever it settles. So it is searched
for rather than chosen: among the frames where the shipped pane and the reference disagree
(otherwise the example shows nothing), take the one that the fewest wrong readings get wrong.

    python3 -u authoring/row-anchor-pass/example.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

for _build in emit.BUILDERS:
    _build()


def main():
    ship = lab.inproc(lab.tree(None))
    docs = ["tiny.txt", "pair.txt"]
    texts = {d: (lab.SRC / "evs" / d).read_text(encoding="utf-8") for d in docs}
    shipped = {d: ship.run(texts[d]) for d in docs}
    ref = lab.inproc(lab.tree(lab.SOL))
    right = {d: ref.run(texts[d]) for d in docs}

    wrong = {d: [] for d in docs}
    for name, files in sorted(emit.READINGS.items()):
        mod = lab.inproc(lab.tree(lab.SOL, files))
        for d in docs:
            try:
                wrong[d].append((name, mod.run(texts[d])))
            except Exception:
                wrong[d].append((name, None))

    rows = []
    for d in docs:
        for i, line in enumerate(right[d]):
            if not line.startswith("f "):
                continue
            if i >= len(shipped[d]) or shipped[d][i] == line:
                continue
            settles = [n for n, out in wrong[d]
                       if out is None or i >= len(out) or out[i] != line]
            rows.append((len(settles), d, i, line, shipped[d][i], settles))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    for count, d, i, line, was, settles in rows[:12]:
        print("%-9s frame %-3d settles %2d  %s" % (d, i, count, ",".join(settles[:6])))
        print("      shipped %s" % was)
        print("      correct %s" % line)


if __name__ == "__main__":
    main()
