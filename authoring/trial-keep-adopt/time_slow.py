"""The stated limit, against the two readings that are exactly correct and cannot afford it.

Both print the reference's trace on everything they finish, so nothing but the clock separates
them. Run with -u: a harness whose output is the measurement must not sit in a buffer.
"""
import pathlib
import sys
import tempfile
import time

import lab

TASK = lab.TASK
sys.path.insert(0, str(TASK / "tests"))
import gen  # noqa: E402

ROOM = pathlib.Path(__file__).resolve().parent / "readings"


def write(lines):
    room = pathlib.Path(tempfile.mkdtemp(prefix="tka-time-"))
    path = room / "p.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def main():
    cap = float(sys.argv[1]) if len(sys.argv) > 1 else 200.0
    want = sys.argv[2] if len(sys.argv) > 2 else "wide"
    progs = [(fam, name, lines) for fam, name, lines in gen.programs("slow", 1)
             if fam == want][:1]
    trees = [("reference", lab.ref()), ("shipped", lab.shipped())]
    for name in ("pre-copy", "no-memo"):
        trees.append((name, lab.tree(ROOM / name)))
    for fam, pname, lines in progs:
        path = write(lines)
        print("== %s (%d lines)" % (pname, len(lines)), flush=True)
        base = None
        for label, here in trees:
            t0 = time.time()
            try:
                out = lab.run(here, path, timeout=cap)
                d = time.time() - t0
                same = "" if base is None else (" same trace" if out == base else " DIFFERENT")
                if base is None:
                    base = out
                print("   %-10s %8.2fs %7d lines%s" % (label, d, len(out), same), flush=True)
            except Exception as exc:
                print("   %-10s  over %.0fs (%s)" % (label, cap, type(exc).__name__), flush=True)


if __name__ == "__main__":
    main()
