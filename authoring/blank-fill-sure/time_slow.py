import os, sys, time, signal, resource


def peak():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024


HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tasks", "blank-fill-sure")
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(TASK, "tests"))
import gen, tree
name, fam, limit = sys.argv[1], sys.argv[2], int(sys.argv[3])
run = tree.runner(os.path.join(HERE, "readings", name) if name != "reference" else os.path.join(TASK, "solution"))
progs = [p for p in gen.programs("timing", 1) if p[0] == fam]
def alarm(*_): raise TimeoutError()
signal.signal(signal.SIGALRM, alarm)
for f, n, lines in progs[:1]:
    signal.alarm(limit)
    t0 = time.time()
    try:
        run("\n".join(lines) + "\n"); signal.alarm(0)
        print("%s on %s: %.1fs, peak %d MB" % (name, n, time.time() - t0, peak()), flush=True)
    except TimeoutError:
        print("%s on %s: killed at %ds, peak %d MB" % (name, n, limit, peak()), flush=True)
    except MemoryError:
        print("%s on %s: MemoryError after %.1fs, peak %d MB" % (name, n, time.time() - t0, peak()), flush=True)
