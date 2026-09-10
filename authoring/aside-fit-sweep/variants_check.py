import pathlib, subprocess, sys, shutil, tempfile, json
HERE = pathlib.Path("authoring/aside-fit-sweep")
TASK = pathlib.Path("tasks/aside-fit-sweep")
sys.path.insert(0, str(HERE))
import readings as R
scratch = pathlib.Path(tempfile.mkdtemp())
good = R.measure(None, "variants", 10, scratch/"ref.json")
for v in sorted((HERE/"variants").iterdir()):
    got = R.measure(v, "variants", 10, scratch/(v.name+".json"))
    bad = [k for k in good["res"] if good["res"][k] != got["res"].get(k)]
    print("%-10s differing %d of %d   %.1fs" % (v.name, len(bad), len(good["res"]), got["secs"]), bad[:3])
