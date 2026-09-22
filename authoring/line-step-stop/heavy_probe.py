import json, random, sys, time
from lab import forge
import bench
rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
t = time.time()
sess = []
for i in range(n):
    s = forge.heavy_session(rng)
    sess.append(s)
    print("built heavy %d: volume %d, in-frame %d, %d cmds, %.1fs" % (i, s["volume"], s["in_frame"], len(s["cmds"]), time.time() - t), flush=True)
json.dump(sess, open("/tmp/claude-0/-home-user-project-caesar/97512dba-3dc5-5d6c-98db-3058c9acf124/scratchpad/heavy_probe.json", "w"))
tot = sum(s["volume"] for s in sess)
for v, cap in (("reference", 600), ("half", 300), ("slow", 300)):
    res, dt = bench.play_all(v, sess, timeout=cap)
    if res is None:
        print("%s: TIMEOUT after %ds on %d instructions" % (v, cap, tot), flush=True)
        continue
    bad = bench.compare(sess, res)
    print("%s: %d differ, %.1fs total, per-session %s" % (v, len(bad), dt, [round(r["secs"], 2) for r in res]), flush=True)
