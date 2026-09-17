"""Print each enumerated program with what the reference and the model make of it."""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tasks/queue-hold-drop/tests"))
sys.path.insert(0, str(HERE.parent.parent / "tasks/queue-hold-drop/tests/seal"))
sys.path.insert(0, str(HERE))
import cases, model, lab

only = sys.argv[1:] or cases.ORDER
bad = 0
for name in only:
    lines = cases.ops(name)
    want = model.expect(lines)
    got = lab.run(lines, "ref")
    flag = "" if got == want else "   <-- REFERENCE DIFFERS"
    print("== %s%s" % (name, flag))
    for l in lines:
        print("   | %s" % l)
    for l in want:
        print("   > %s" % l)
    if got != want:
        bad += 1
        for l in got:
            print("   R %s" % l)
print("%d of %d differ" % (bad, len(only)))
