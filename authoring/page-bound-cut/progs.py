"""Write the sample programs that ship under /app/progs.

They come from the same family builders as the graded population but at a fixed authoring
seed, so they are different instances from the ones a run is marked on. `bulk` is written at
the size of the graded large programs, so timing an implementation against it locally
measures the real thing rather than a scaled-down guess.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

_c, gen, _m = lab.sealed()

WANTED = [
    ("few", (None, gen.SHARE, 8, 10, "churn", 0.45, 30, 96, 44), 8101),
    ("mix", (None, gen.WIDE, 3, 7, "purge", 0.9, 70, 64, 24), 8102),
    ("thin", (None, gen.SHARE, 8, 10, "purge", 0.95, 90, 40, 10), 8103),
    ("bulk", (None, gen.SHARE, 8, 10, "churn", 0.45, 60000, 96, 32), 8104),
]


def main():
    out = lab.SRC / "progs"
    out.mkdir(parents=True, exist_ok=True)
    for name, row, seed in WANTED:
        row = (name,) + row[1:]
        body = gen.build(row, seed)
        if "\r" in body:
            raise SystemExit("progs: carriage return in %s" % name)
        (out / ("%s.txt" % name)).write_text(body, encoding="utf-8", newline="\n")
        print("%-6s %7d ops  %8d bytes" % (name, body.count("\n") - 1, len(body)))


if __name__ == "__main__":
    main()
