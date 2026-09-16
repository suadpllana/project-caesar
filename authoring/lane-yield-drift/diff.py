import sys, os, importlib.util, tempfile, shutil, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASK = os.path.join(ROOT, "tasks", "lane-yield-drift")

def load_engine(tag, patch_dir):
    d = tempfile.mkdtemp(prefix="lyd-%s-" % tag)
    app = os.path.join(d, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), app)
    if patch_dir:
        for f in os.listdir(patch_dir):
            if f.endswith(".py"):
                shutil.copyfile(os.path.join(patch_dir, f), os.path.join(app, "sked", f))
    sys.path.insert(0, app)
    import importlib
    for m in list(sys.modules):
        if m == "sked" or m.startswith("sked."):
            del sys.modules[m]
    sked_read = importlib.import_module("sked.read")
    sked_emit = importlib.import_module("sked.emit")
    sked_lane = importlib.import_module("sked.lane")
    def run(text):
        return sked_emit.lines(sked_lane.run(sked_read.parse(text)))
    return run, d

sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))
import gen, model

def main():
    nonce = sys.argv[1] if len(sys.argv) > 1 else "diffprobe"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    ref, d = load_engine("ref", os.path.join(TASK, "solution"))
    bad = 0
    tot = 0
    evs = 0
    fams = {}
    for name, text in gen.plans(nonce, per):
        tot += 1
        a = ref(text)
        b = model.trace(text)
        evs += len(a)
        fams.setdefault(name.split("-")[0], [0, 0])
        fams[name.split("-")[0]][0] += 1
        fams[name.split("-")[0]][1] += len(a)
        if a != b:
            bad += 1
            if bad <= 3:
                print("MISMATCH", name)
                print(text)
                for i in range(max(len(a), len(b))):
                    x = a[i] if i < len(a) else "-"
                    y = b[i] if i < len(b) else "-"
                    if x != y:
                        print("  ref %-28s model %s" % (x, y))
                        break
    print("plans %d  mismatches %d  events %d" % (tot, bad, evs))
    for k in sorted(fams):
        print("  %-6s plans %3d  mean events %.1f" % (k, fams[k][0], fams[k][1] / fams[k][0]))
    shutil.rmtree(d, ignore_errors=True)

main()
