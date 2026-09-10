"""Search for the worked example the brief prints verbatim.

It has to show the shipped allocator getting exactly one line wrong - the last one - and it has
to decide as few of the wrong readings as possible, because a worked example that separates six
readings is an oracle for six rules the agent should have had to reason about.
"""
import itertools, pathlib, random, shutil, subprocess, sys, tempfile, json
HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "aside-fit-sweep"
PARTS = ("find.py", "cut.py", "side.py", "back.py", "edge.py")
RUN = '''
import json, sys
sys.path.insert(0, sys.argv[1])
import ops
from reg import live, text
progs = json.load(open(sys.argv[2]))
res = []
for lines in progs:
    span, part, body = text.parse(lines)
    h = live.Pool(span, part); out = []
    try:
        for line in body:
            ops.ex(h, tuple(line.split()), out)
    except Exception as exc:
        out = ["RAISED %s" % exc]
    res.append(out)
json.dump(res, open(sys.argv[3], "w"))
'''

def stage(overlay):
    room = pathlib.Path(tempfile.mkdtemp(prefix="afs-e-"))
    app = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    if overlay is not None:
        for p in PARTS:
            if (overlay / p).is_file():
                shutil.copy(overlay / p, app / "pool" / p)
    (room / "r.py").write_text(RUN)
    return room, app

def batch(overlay, progs, scratch, tag):
    room, app = stage(overlay)
    pin = scratch / "in.json"; pin.write_text(json.dumps(progs))
    pout = scratch / ("%s.json" % tag)
    subprocess.run([sys.executable, str(room / "r.py"), str(app), str(pin), str(pout)], check=True)
    shutil.rmtree(room, ignore_errors=True)
    return json.loads(pout.read_text())

def gen(rng):
    span, part = rng.choice([(2048, 512), (1024, 512), (2048, 1024)])
    lines = ["span %d" % span, "part %d" % part]
    live_ids = []
    for _ in range(rng.randrange(4, 9)):
        r = rng.random()
        if r < 0.55 or not live_ids:
            name = "abcdefg"[rng.randrange(7)]
            lines.append("get %s %d" % (name, rng.choice(
                [8, 24, 48, 56, 64, 120, 128, 200, 248, 256, 264, 448, 504, 512])))
            live_ids.append(name)
        elif r < 0.8:
            lines.append("put %s" % rng.choice(live_ids))
        elif r < 0.9:
            lines.append("fit %s %d" % (rng.choice(live_ids), rng.choice([16, 56, 128, 192, 304])))
        else:
            lines.append("sweep")
    return lines

def main():
    rng = random.Random(11)
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="afs-ex-"))
    progs = [gen(rng) for _ in range(4000)]
    ship = batch(None, progs, scratch, "ship")
    good = batch(TASK / "solution", progs, scratch, "good")
    keep = []
    for i, lines in enumerate(progs):
        a, b = ship[i], good[i]
        if len(a) != len(b) or not b or a == b:
            continue
        if a[:-1] == b[:-1] and a[-1] != b[-1]:
            keep.append(i)
    print("candidates with exactly one wrong line, at the end: %d" % len(keep))
    names = sorted(p.name for p in (HERE / "readings").iterdir())
    sub = [progs[i] for i in keep]
    hits = {}
    for name in names:
        got = batch(HERE / "readings" / name, sub, scratch, name)
        for k, lines in enumerate(sub):
            if got[k] != [good[keep[k]]][0]:
                hits.setdefault(k, []).append(name)
    ranked = sorted(range(len(sub)), key=lambda k: (len(hits.get(k, [])), len(sub[k])))
    for k in ranked[:8]:
        i = keep[k]
        print("---- decides %d readings %s" % (len(hits.get(k, [])), hits.get(k, [])))
        print("     %s" % " | ".join(progs[i]))
        print("     shipped last: %r   correct last: %r" % (ship[i][-1], good[i][-1]))
    shutil.rmtree(scratch, ignore_errors=True)

main()
