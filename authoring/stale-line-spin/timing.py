"""Time the sealed model (frozen-stretch skip) and the plain stepper on the scale families."""
import sys, time, signal
sys.path.insert(0, "tasks/stale-line-spin/tests/seal")
sys.path.insert(0, "tasks/stale-line-spin/tests")
sys.path.insert(0, "authoring/stale-line-spin")
import model, gen, naive

seed = sys.argv[1] if len(sys.argv) > 1 else "t1"
naive_cap = int(sys.argv[2]) if len(sys.argv) > 2 else 0

class Out(Exception):
    pass

def alarm(*_):
    raise Out()

signal.signal(signal.SIGALRM, alarm)
for fam, name, lines in gen.programs(seed, 0):
    head = [l for l in lines[:3]]
    t0 = time.time()
    out = model.expect(lines)
    tm = time.time() - t0
    ends = [l for l in out if l.startswith("blk")]
    last = max(int(l.split()[7]) for l in ends) if ends else -1
    print("%s %s model %.2fs blocks=%d last_exit=%d hang=%s" % (
        name, head[0], tm, len(ends), last, any(l.startswith("hang") for l in out)), flush=True)
    if naive_cap:
        signal.alarm(naive_cap)
        t0 = time.time()
        try:
            n = naive.run(lines)
            print("   naive %.1fs agree=%s" % (time.time() - t0, n == out), flush=True)
        except Out:
            print("   naive still running after %ds" % naive_cap, flush=True)
        signal.alarm(0)
