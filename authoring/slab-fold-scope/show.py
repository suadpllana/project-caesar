"""Run every enumerated case through the reference and the sealed model and compare.

Writes nothing inside the bundle. Output is the measurement, so it flushes.
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import model  # noqa: E402


def under(over, lines):
    room = pathlib.Path(tempfile.mkdtemp(prefix="sfs-prog-"))
    prog = room / "p.txt"
    prog.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return lab.run(over, prog)


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else None
    ref = lab.tree(lab.TASK / "solution")
    ship = lab.tree()
    same = 0
    for name in cases.ORDER:
        if want and want != name:
            continue
        lines = cases.ops(name)
        got = under(ref, lines)
        mod = model.expect(lines)
        shipped = under(ship, lines)
        flag = "OK " if got == mod else "MODEL DIFFERS"
        if got == shipped:
            same += 1
            flag += " shipped-agrees"
        print("== %-16s %s" % (name, flag), flush=True)
        if want or got != mod:
            for i, line in enumerate(got):
                other = mod[i] if i < len(mod) else "-"
                shp = shipped[i] if i < len(shipped) else "-"
                tail = "" if line == shp else "      shipped: %s" % shp
                bad = "" if line == other else "   MODEL: %s" % other
                print("   %s%s%s" % (line, bad, tail))
    print("\n%d of %d cases the shipped engine already gets right"
          % (same, len(cases.ORDER)), flush=True)


if __name__ == "__main__":
    main()
