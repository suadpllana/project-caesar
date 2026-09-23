import sys, time
sys.path.insert(0, '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/work')
import gen2, genwide
texts = []
for f in ['wide', 'wide', 'wide', 'deep', 'deep', 'deep']:
    texts.append(open('../app/segs/%s.txt' % f).read())
for s in range(308):
    texts.append(genwide.gen(1000 + s, N=2000) if s % 4 == 0 else gen2.gen(5000 + s))
for s in range(60):
    texts.append(gen2.gen(9000 + s))
sys.path.insert(0, '/tmp/claude-0/-home-user-project-caesar/4a834684-610b-57cb-81ee-0ddb057c24c0/scratchpad/p4_2/app')
import run_scan
t = time.time()
n = 0
for tx in texts:
    n += len(run_scan.run(tx))
print('files', len(texts), 'lines', n, 'seconds %.2f' % (time.time() - t))
