"""Write authoring/variants/ from the reference plus one declared override each.

Hand-copied variants drift the moment the reference changes, and the symptom is every
correct implementation disagreeing at once, which reads like a broken reference. Generating
them makes that impossible.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import emit  # noqa: E402

OUT = HERE / "variants"


def main():
    src = emit.ref_source()
    OUT.mkdir(exist_ok=True)
    n = 0
    for name, (note, files) in sorted(emit.right(src).items()):
        d = OUT / name
        d.mkdir(exist_ok=True)
        for f in emit.FILES:
            (d / f).write_text(files[f], encoding="utf-8", newline="\n")
        (d / "README.txt").write_text(note + "\n", encoding="utf-8", newline="\n")
        n += 1
    print("wrote %d variants" % n)


if __name__ == "__main__":
    main()
