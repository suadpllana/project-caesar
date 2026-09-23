"""Compare the implementation under app/ with the literal model on random files."""
import importlib
import sys
import traceback

W = '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/work'
A = '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/app'
sys.path.insert(0, W)
import gen  # noqa: E402
import model  # noqa: E402

# load the implementation's modules fresh from app/
for k in list(sys.modules):
    if k == 'scn' or k.startswith('scn.'):
        del sys.modules[k]
sys.path.insert(0, A)
import run_scan  # noqa: E402

lo = int(sys.argv[1])
hi = int(sys.argv[2])
bad = 0
for seed in range(lo, hi):
    text = gen.gen(seed)
    try:
        a = run_scan.run(text)
    except Exception:
        print('impl crash', seed)
        traceback.print_exc()
        bad += 1
        continue
    b = model.model(text)
    if a != b:
        bad += 1
        print('DIFF seed', seed)
        if bad <= 3:
            import difflib
            for l in difflib.unified_diff(b, a, 'model', 'impl', lineterm='', n=2):
                print(l)
        if bad > 20:
            break
print('done', hi - lo, 'bad', bad)
