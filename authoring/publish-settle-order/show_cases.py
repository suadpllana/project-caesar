import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tasks" / "publish-settle-order" / "tests"))
import cases  # noqa: E402
import lab  # noqa: E402

which = sys.argv[1] if len(sys.argv) > 1 else "ref"
overlay = None if which == "ship" else pathlib.Path(which)
lb = lab.Lab(overlay)
for name in cases.ORDER:
    print("== %s" % name)
    for ln in lb.run(cases.ops(name)):
        print("   " + ln)
lb.close()
