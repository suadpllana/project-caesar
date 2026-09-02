"""Which part of the ledger separates each wrong reading, and on how many streams.

Two things this is for. A row kind that separates nothing is pure liability: it cannot
catch a wrong answer and it can fail a right one. And a reading that differs from the
reference on a handful of streams out of hundreds is a lottery ticket rather than a test
of expertise, so the per-reading stream count is printed beside the row kinds.

    python3 authoring/field_report.py [generated-count]
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import emit  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402

KINDS = ("cn", "em", "dp", "db", "rl", "sh", "state")


def kinds_of(got, want):
    hit = set()
    if got["state"] != want["state"]:
        hit.add("state")
    a, b = got["log"], want["log"]
    for n in range(max(len(a), len(b))):
        x = a[n].split() if n < len(a) else []
        y = b[n].split() if n < len(b) else []
        if x != y:
            for row in (x, y):
                if len(row) > 1 and row[1] in KINDS:
                    hit.add(row[1])
    return hit


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 200
    streams = scen.cases() + gen.build("fields", count)
    want = {n: oracle.play(t) for n, t in streams}
    src = {f: emit.strip_doc(v) for f, v in emit.ref_source().items()}

    seen = {}
    print("%-16s %-7s %s" % ("reading", "streams", "row kinds that differ"))
    for name, (_note, files) in sorted(emit.variants(src).items()):
        d = pathlib.Path(harness.stage(TASK / "environment" / "app_src", None)).parent / "policy"
        d.mkdir(exist_ok=True)
        for f in emit.FILES:
            (d / f).write_text(files[f], encoding="utf-8", newline="\n")
        tree = harness.stage(TASK / "environment" / "app_src", d)
        got = harness.drive(tree, streams)
        diff = set()
        n = 0
        for sname, _ in streams:
            g, w = got[sname], want[sname]
            if g["err"] or g["log"] != w["log"] or g["state"] != w["state"]:
                n += 1
                diff |= kinds_of(g, w)
        for k in diff:
            seen[k] = seen.get(k, 0) + 1
        print("%-16s %3d/%-3d %s" % (name, n, len(streams), " ".join(sorted(diff)) or "NONE"))

    dead = [k for k in KINDS if k not in seen]
    print("\nrow kinds separating nothing: %s" % (", ".join(dead) if dead else "none"))
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
