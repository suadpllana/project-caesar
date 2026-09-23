import sys, time
W = '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/work'
A = '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/app'
sys.path.insert(0, W)
import genwide, model
for k in list(sys.modules):
    if k == 'scn' or k.startswith('scn.'):
        del sys.modules[k]
sys.path.insert(0, A)
import run_scan
N = int(sys.argv[3]) if len(sys.argv) > 3 else 400
bad = 0
for seed in range(int(sys.argv[1]), int(sys.argv[2])):
    text = genwide.gen(seed, N=N)
    t = time.time(); a = run_scan.run(text); ta = time.time() - t
    t = time.time(); b = model.model(text); tb = time.time() - t
    ok = a == b
    if not ok:
        bad += 1
        for i, (x, y) in enumerate(zip(b, a)):
            if x != y:
                print('first diff at', i, 'model', x, 'impl', y); break
        else:
            print('length differs', len(b), len(a))
    print(seed, 'ok' if ok else 'DIFF', len(a), 'lines', '%.2fs %.2fs' % (ta, tb), flush=True)
print('bad', bad)
