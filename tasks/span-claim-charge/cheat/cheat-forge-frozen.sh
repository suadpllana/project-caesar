#!/bin/bash
# carries the frozen answers for the enumerated programs
set -euo pipefail

cat > /app/store/dev.py <<'PYEOF'
import json

_KEY = json.loads('{"n a\\nw a/f 0 4\\nw a/g 0 6\\nw a/h 0 4\\nw a/i 0 6\\nx a/f\\nx a/h\\nf\\nw a/j 0 4\\nm a/j\\nf": ["n a", "w a/f new=4 keep=0 rel=0", "w a/g new=6 keep=0 rel=0", "w a/h new=4 keep=0 rel=0", "w a/i new=6 keep=0 rel=0", "x a/f rel=4", "x a/h rel=4", "f free=12 runs=3 big=4", "w a/j new=4 keep=0 rel=0", "m a/j size=4 0:0+0:4", "f free=8 runs=2 big=4"], "n a\\nw a/f 0 6\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/f\\nx a/h\\nf\\nw a/j 0 4\\nm a/j\\nf": ["n a", "w a/f new=6 keep=0 rel=0", "w a/g new=3 keep=0 rel=0", "w a/h new=4 keep=0 rel=0", "w a/i new=3 keep=0 rel=0", "x a/f rel=6", "x a/h rel=4", "f free=18 runs=3 big=8", "w a/j new=4 keep=0 rel=0", "m a/j size=4 0:9+0:4", "f free=14 runs=2 big=8"], "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nw a/i 0 4\\nx a/f\\nx a/h\\nf\\nw a/j 0 4\\nm a/j": ["n a", "w a/f new=4 keep=0 rel=0", "w a/g new=4 keep=0 rel=0", "w a/h new=4 keep=0 rel=0", "w a/i new=4 keep=0 rel=0", "x a/f rel=4", "x a/h rel=4", "f free=16 runs=3 big=8", "w a/j new=4 keep=0 rel=0", "m a/j size=4 0:0+0:4"], "n a\\nw a/f 0 8\\nw a/g 0 5\\nf\\nw a/g 0 4\\nm a/g\\nf": ["n a", "w a/f new=8 keep=0 rel=0", "w a/g err=noroom", "f free=4 runs=1 big=4", "w a/g new=4 keep=0 rel=0", "m a/g size=4 0:8+0:4", "f free=0 runs=0 big=0"], "n a\\nw a/f 0 3\\nw a/g 0 5\\nw a/h 0 3\\nw a/i 0 9\\nx a/f\\nx a/h\\nx a/i\\nf\\nw a/j 0 12\\nm a/j\\nf": ["n a", "w a/f new=3 keep=0 rel=0", "w a/g new=5 keep=0 rel=0", "w a/h new=3 keep=0 rel=0", "w a/i new=9 keep=0 rel=0", "x a/f rel=3", "x a/h rel=3", "x a/i rel=9", "f free=15 runs=2 big=12", "w a/j new=12 keep=0 rel=0", "m a/j size=12 0:8+0:12", "f free=3 runs=1 big=3"], "n a\\nw a/f 0 4\\nw a/g 0 2\\nw a/h 0 4\\nw a/i 0 6\\nx a/g\\nx a/i\\nf\\nw a/j 0 8\\nm a/j\\nf": ["n a", "w a/f new=4 keep=0 rel=0", "w a/g new=2 keep=0 rel=0", "w a/h new=4 keep=0 rel=0", "w a/i new=6 keep=0 rel=0", "x a/g rel=2", "x a/i rel=6", "f free=8 runs=2 big=6", "w a/j new=8 keep=0 rel=0", "m a/j size=8 0:10+0:6 6:4+0:2", "f free=0 runs=0 big=0"], "n a\\nw a/f 0 4\\nt a/f 0\\nm a/f\\nf\\nx a/f\\nm a/f": ["n a", "w a/f new=4 keep=0 rel=0", "t a/f rel=4", "m a/f size=0", "f free=16 runs=1 big=16", "x a/f rel=0", "m a/f err=nosuch"], "n a\\nw a/f 0 8\\ns a/f 0 4 a/g 0\\ns a/f 4 4 a/g 4\\nm a/g\\nm a/f": ["n a", "w a/f new=8 keep=0 rel=0", "s a/g rel=0", "s a/g rel=0", "m a/g size=8 0:0+0:8", "m a/f size=8 0:0+0:8"], "n a\\nn b\\nw a/f 0 6\\ns a/f 0 6 b/g 0\\nd a\\nf\\nd b\\nf": ["n a", "n b", "w a/f new=6 keep=0 rel=0", "s b/g rel=0", "d a rel=0", "f free=58 runs=1 big=58", "d b rel=6", "f free=64 runs=1 big=64"], "n a\\nw a/f 0 6\\np a b\\nw b/f 0 3\\nf\\nd b\\nf\\nc a": ["n a", "w a/f new=6 keep=0 rel=0", "p b items=1", "w b/f new=3 keep=0 rel=0", "f free=55 runs=1 big=55", "d b rel=3", "f free=58 runs=1 big=58", "c a ref=6 excl=6"], "n a\\nw a/f 0 6\\nw a/g 0 6\\nx a/f\\nf\\nx a/g\\nf\\nc a": ["n a", "w a/f new=6 keep=0 rel=0", "w a/g new=6 keep=0 rel=0", "x a/f rel=6", "f free=26 runs=2 big=20", "x a/g rel=6", "f free=32 runs=1 big=32", "c a ref=0 excl=0"], "n a\\nn a\\nw a/f 0 4\\np a b\\np a b\\np c d\\nc a": ["n a", "n a err=dup", "w a/f new=4 keep=0 rel=0", "p b items=1", "p b err=dup", "p d err=nosuch", "c a ref=4 excl=0"], "n a\\nw a/f 0 4\\nw a/f 6 2\\nm a/f\\nw a/g 3 2\\nf\\ns a/f 0 2 a/h 4": ["n a", "w a/f new=4 keep=0 rel=0", "w a/f err=gap", "m a/f size=4 0:0+0:4", "w a/g err=gap", "f free=28 runs=1 big=28", "s a/h err=gap"], "n a\\nw z/f 0 4\\nc z\\ng a,z\\nd z\\nx a/f\\nt a/f 2\\nv a/f\\nm a/f\\np z b": ["n a", "w z/f err=nosuch", "c z err=nosuch", "g a,z err=nosuch", "d z err=nosuch", "x a/f err=nosuch", "t a/f err=nosuch", "v a/f err=nosuch", "m a/f err=nosuch", "p b err=nosuch"], "n a\\nw a/f 0 4\\nw a/f 0 0\\nt a/f 9\\ns a/f 2 4 a/g 0\\nm a/f\\nf": ["n a", "w a/f new=4 keep=0 rel=0", "w a/f err=range", "t a/f err=range", "s a/g err=range", "m a/f size=4 0:0+0:4", "f free=28 runs=1 big=28"], "n a\\nw a/f 0 8\\ns a/f 0 4 a/f 4\\nc a\\ng a": ["n a", "w a/f new=8 keep=0 rel=0", "s a/f rel=0", "c a ref=8 excl=8", "g a rel=8"], "n a\\nn b\\nw a/f 0 8\\ns a/f 0 4 b/g 0\\nc a\\nc b\\ng a\\ng b\\ng a,b": ["n a", "n b", "w a/f new=8 keep=0 rel=0", "s b/g rel=0", "c a ref=8 excl=0", "c b ref=8 excl=0", "g a rel=0", "g b rel=0", "g a,b rel=8"], "n a\\nn b\\nw a/f 0 5\\nw b/g 0 5\\ns a/f 0 5 b/h 0\\nc a\\ng a\\ng b\\ng a,b": ["n a", "n b", "w a/f new=5 keep=0 rel=0", "w b/g new=5 keep=0 rel=0", "s b/h rel=0", "c a ref=5 excl=0", "g a rel=0", "g b rel=5", "g a,b rel=10"], "n a\\nw a/f 0 6\\np a b\\np a c\\nw c/f 0 6\\ng a\\ng b\\ng a,b\\ng a,b,c": ["n a", "w a/f new=6 keep=0 rel=0", "p b items=1", "p c items=1", "w c/f new=6 keep=0 rel=0", "g a rel=0", "g b rel=0", "g a,b rel=6", "g a,b,c rel=12"], "n a\\nn b\\nw a/f 0 12\\ns a/f 4 4 b/g 0\\nw a/f 0 12\\nm a/f\\nf": ["n a", "n b", "w a/f new=12 keep=0 rel=0", "s b/g rel=0", "w a/f new=4 keep=8 rel=0", "m a/f size=12 0:0+0:4 4:12+0:4 8:0+8:4", "f free=16 runs=1 big=16"], "n a\\nw a/f 0 6\\nt a/f 0\\nw a/f 0 6\\nm a/f\\nf": ["n a", "w a/f new=6 keep=0 rel=0", "t a/f rel=6", "w a/f new=6 keep=0 rel=0", "m a/f size=6 0:0+0:6", "f free=26 runs=1 big=26"], "n a\\nw a/f 0 8\\ns a/f 0 4 a/f 4\\nm a/f\\nw a/f 0 4\\nm a/f\\nf": ["n a", "w a/f new=8 keep=0 rel=0", "s a/f rel=0", "m a/f size=8 0:0+0:4 4:0+0:4", "w a/f new=4 keep=0 rel=0", "m a/f size=8 0:8+0:4 4:0+0:4", "f free=20 runs=1 big=20"], "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nw a/f 2 4\\nm a/f\\nf": ["n a", "n b", "w a/f new=8 keep=0 rel=0", "s b/g rel=0", "w a/f new=4 keep=0 rel=0", "m a/f size=8 0:0+0:2 2:8+0:4 6:0+6:2", "f free=20 runs=1 big=20"], "n a\\nw a/f 0 8\\nw a/f 2 4\\nm a/f\\nf\\nw a/f 0 8\\nf": ["n a", "w a/f new=8 keep=0 rel=0", "w a/f new=0 keep=4 rel=0", "m a/f size=8 0:0+0:8", "f free=24 runs=1 big=24", "w a/f new=0 keep=8 rel=0", "f free=24 runs=1 big=24"], "n a\\nw a/f 0 6\\nw a/f 4 6\\nm a/f\\nf": ["n a", "w a/f new=6 keep=0 rel=0", "w a/f new=4 keep=2 rel=0", "m a/f size=10 0:0+0:6 6:6+0:4", "f free=22 runs=1 big=22"], "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g\\nx a/i\\nf\\nw a/j 0 12\\nw a/k 0 6\\ns a/k 0 6 b/x 0\\nw a/k 1 1\\nw a/k 4 1\\nm a/k\\nf": ["n a", "n b", "w a/f new=4 keep=0 rel=0", "w a/g new=3 keep=0 rel=0", "w a/h new=4 keep=0 rel=0", "w a/i new=3 keep=0 rel=0", "x a/g rel=3", "x a/i rel=3", "f free=24 runs=2 big=21", "w a/j new=12 keep=0 rel=0", "w a/k new=6 keep=0 rel=0", "s b/x rel=0", "w a/k new=1 keep=0 rel=0", "w a/k new=1 keep=0 rel=0", "m a/k size=6 0:23+0:1 1:4+0:1 2:23+2:2 4:5+0:1 5:23+5:1", "f free=4 runs=2 big=3"], "n a\\nw a/f 0 6\\nw a/g 0 6\\nw a/h 0 6\\nx a/f\\nx a/h\\nf\\nx a/g\\nf": ["n a", "w a/f new=6 keep=0 rel=0", "w a/g new=6 keep=0 rel=0", "w a/h new=6 keep=0 rel=0", "x a/f rel=6", "x a/h rel=6", "f free=18 runs=2 big=12", "x a/g rel=6", "f free=24 runs=1 big=24"], "n a\\nw a/f 0 8\\nw a/g 0 2\\nc a\\nf\\nm a/g": ["n a", "w a/f new=8 keep=0 rel=0", "w a/g err=noroom", "c a ref=8 excl=8", "f free=0 runs=0 big=0", "m a/g err=nosuch"], "n a\\nw a/f 0 8\\ns a/f 0 2 a/g 0\\ns a/f 4 2 a/h 0\\nc a": ["n a", "w a/f new=8 keep=0 rel=0", "s a/g rel=0", "s a/h rel=0", "c a ref=8 excl=8"], "n a\\nn b\\nw a/f 0 10\\ns a/f 2 3 b/g 0\\nc a\\nc b\\ng b": ["n a", "n b", "w a/f new=10 keep=0 rel=0", "s b/g rel=0", "c a ref=10 excl=0", "c b ref=10 excl=0", "g b rel=0"], "n a\\nw a/f 0 6\\nw a/g 0 10\\ns a/f 0 3 a/f 3\\nf\\nw a/f 0 6\\nm a/f\\nf": ["n a", "w a/f new=6 keep=0 rel=0", "w a/g new=10 keep=0 rel=0", "s a/f rel=0", "f free=0 runs=0 big=0", "w a/f new=6 keep=0 rel=6", "m a/f size=6 0:0+0:6", "f free=0 runs=0 big=0"], "n a\\nn b\\nw a/f 0 12\\ns a/f 0 6 b/g 0\\nf\\nw a/f 6 6\\nm a/f\\nf": ["n a", "n b", "w a/f new=12 keep=0 rel=0", "s b/g rel=0", "f free=0 runs=0 big=0", "w a/f new=0 keep=6 rel=0", "m a/f size=12 0:0+0:12", "f free=0 runs=0 big=0"], "n a\\nn b\\nw a/f 0 12\\ns a/f 0 12 b/g 0\\nw a/f 0 12\\nm a/f\\nf": ["n a", "n b", "w a/f new=12 keep=0 rel=0", "s b/g rel=0", "w a/f err=noroom", "m a/f size=12 0:0+0:12", "f free=0 runs=0 big=0"], "n a\\nn b\\nw a/f 0 6\\nw b/g 0 6\\nf\\ns a/f 0 6 b/g 0\\nf\\nc a\\nc b": ["n a", "n b", "w a/f new=6 keep=0 rel=0", "w b/g new=6 keep=0 rel=0", "f free=20 runs=1 big=20", "s b/g rel=6", "f free=26 runs=1 big=26", "c a ref=6 excl=0", "c b ref=6 excl=0"], "n a\\nn b\\nw a/f 0 9\\nw b/g 0 9\\ns a/f 3 3 b/g 3\\nm b/g\\nf\\nc b": ["n a", "n b", "w a/f new=9 keep=0 rel=0", "w b/g new=9 keep=0 rel=0", "s b/g rel=0", "m b/g size=9 0:9+0:3 3:0+3:3 6:9+6:3", "f free=14 runs=1 big=14", "c b ref=18 excl=9"], "n a\\nw a/f 0 8\\ns a/f 0 6 a/f 2\\nm a/f\\nf\\nc a": ["n a", "w a/f new=8 keep=0 rel=0", "s a/f rel=0", "m a/f size=8 0:0+0:2 2:0+0:6", "f free=24 runs=1 big=24", "c a ref=8 excl=8"], "n a\\nw a/f 0 5\\nw a/g 0 5\\nx a/f\\nf\\nx a/g\\nf": ["n a", "w a/f new=5 keep=0 rel=0", "w a/g new=5 keep=0 rel=0", "x a/f rel=5", "f free=27 runs=2 big=22", "x a/g rel=5", "f free=32 runs=1 big=32"], "n a\\nn b\\nw a/f 0 9\\ns a/f 0 9 b/g 0\\nw b/g 3 3\\nf\\nx b/g\\nf\\nc a": ["n a", "n b", "w a/f new=9 keep=0 rel=0", "s b/g rel=0", "w b/g new=3 keep=0 rel=0", "f free=20 runs=1 big=20", "x b/g rel=3", "f free=23 runs=1 big=23", "c a ref=9 excl=9"], "n a\\nw a/f 0 6\\nw a/g 0 4\\nc a\\np a b\\nc a\\nc b": ["n a", "w a/f new=6 keep=0 rel=0", "w a/g new=4 keep=0 rel=0", "c a ref=10 excl=10", "p b items=2", "c a ref=10 excl=0", "c b ref=10 excl=0"], "n a\\nw a/f 0 6\\np a b\\nw b/f 0 6\\nc a\\nc b\\nf": ["n a", "w a/f new=6 keep=0 rel=0", "p b items=1", "w b/f new=6 keep=0 rel=0", "c a ref=6 excl=6", "c b ref=6 excl=6", "f free=52 runs=1 big=52"], "n a\\np a b\\nc b\\nw b/f 0 4\\nc a\\nc b": ["n a", "p b items=0", "c b ref=0 excl=0", "w b/f new=4 keep=0 rel=0", "c a ref=0 excl=0", "c b ref=4 excl=4"], "n a\\nw a/f 0 6\\np a b\\np b c\\nc a\\nc b\\nc c\\nw c/f 2 2\\nc a\\nc c": ["n a", "w a/f new=6 keep=0 rel=0", "p b items=1", "p c items=1", "c a ref=6 excl=0", "c b ref=6 excl=0", "c c ref=6 excl=0", "w c/f new=2 keep=0 rel=0", "c a ref=6 excl=0", "c c ref=8 excl=2"], "n a\\nw a/f 0 8\\nt a/f 5\\nf\\nm a/f\\nt a/f 0\\nf": ["n a", "w a/f new=8 keep=0 rel=0", "t a/f rel=0", "f free=24 runs=1 big=24", "m a/f size=5 0:0+0:5", "t a/f rel=8", "f free=32 runs=1 big=32"], "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nt a/f 2\\nf\\nt b/g 2\\nf": ["n a", "n b", "w a/f new=8 keep=0 rel=0", "s b/g rel=0", "t a/f rel=0", "f free=24 runs=1 big=24", "t b/g rel=0", "f free=24 runs=1 big=24"], "n a\\nw a/f 0 8\\nw a/g 0 4\\nx a/g\\nw a/h 0 4\\nx a/f\\nw a/f 0 8\\nf\\nv a/f\\nm a/f\\nf": ["n a", "w a/f new=8 keep=0 rel=0", "w a/g new=4 keep=0 rel=0", "x a/g rel=4", "w a/h new=4 keep=0 rel=0", "x a/f rel=8", "w a/f new=8 keep=0 rel=0", "f free=0 runs=0 big=0", "v a/f new=8 rel=8", "m a/f size=8 0:0+0:8", "f free=0 runs=0 big=0"], "n a\\nw a/f 0 6\\np a b\\nv a/f\\nm a/f\\nc a\\nc b\\nf": ["n a", "w a/f new=6 keep=0 rel=0", "p b items=1", "v a/f new=6 rel=0", "m a/f size=6 0:6+0:6", "c a ref=6 excl=6", "c b ref=6 excl=6", "f free=20 runs=1 big=20"], "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nw a/h 0 4\\nf\\nv a/f\\nm a/f\\nc a\\nf": ["n a", "n b", "w a/f new=8 keep=0 rel=0", "s b/g rel=0", "w a/h new=4 keep=0 rel=0", "f free=0 runs=0 big=0", "v a/f err=noroom", "m a/f size=8 0:0+0:8", "c a ref=12 excl=4", "f free=0 runs=0 big=0"], "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nx a/g\\nf\\nv a/h\\nm a/h\\nf": ["n a", "w a/f new=4 keep=0 rel=0", "w a/g new=4 keep=0 rel=0", "w a/h new=4 keep=0 rel=0", "x a/g rel=4", "f free=24 runs=2 big=20", "v a/h new=4 rel=4", "m a/h size=4 0:4+0:4", "f free=24 runs=1 big=24"]}')
_PRE = set(json.loads('["n a", "n a\\nn a", "n a\\nn a\\nw a/f 0 4", "n a\\nn a\\nw a/f 0 4\\np a b", "n a\\nn a\\nw a/f 0 4\\np a b\\np a b", "n a\\nn a\\nw a/f 0 4\\np a b\\np a b\\np c d", "n a\\nn b", "n a\\nn b\\nw a/f 0 10", "n a\\nn b\\nw a/f 0 10\\ns a/f 2 3 b/g 0", "n a\\nn b\\nw a/f 0 10\\ns a/f 2 3 b/g 0\\nc a", "n a\\nn b\\nw a/f 0 10\\ns a/f 2 3 b/g 0\\nc a\\nc b", "n a\\nn b\\nw a/f 0 12", "n a\\nn b\\nw a/f 0 12\\ns a/f 0 12 b/g 0", "n a\\nn b\\nw a/f 0 12\\ns a/f 0 12 b/g 0\\nw a/f 0 12", "n a\\nn b\\nw a/f 0 12\\ns a/f 0 12 b/g 0\\nw a/f 0 12\\nm a/f", "n a\\nn b\\nw a/f 0 12\\ns a/f 0 6 b/g 0", "n a\\nn b\\nw a/f 0 12\\ns a/f 0 6 b/g 0\\nf", "n a\\nn b\\nw a/f 0 12\\ns a/f 0 6 b/g 0\\nf\\nw a/f 6 6", "n a\\nn b\\nw a/f 0 12\\ns a/f 0 6 b/g 0\\nf\\nw a/f 6 6\\nm a/f", "n a\\nn b\\nw a/f 0 12\\ns a/f 4 4 b/g 0", "n a\\nn b\\nw a/f 0 12\\ns a/f 4 4 b/g 0\\nw a/f 0 12", "n a\\nn b\\nw a/f 0 12\\ns a/f 4 4 b/g 0\\nw a/f 0 12\\nm a/f", "n a\\nn b\\nw a/f 0 4", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g\\nx a/i", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g\\nx a/i\\nf", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g\\nx a/i\\nf\\nw a/j 0 12", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g\\nx a/i\\nf\\nw a/j 0 12\\nw a/k 0 6", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g\\nx a/i\\nf\\nw a/j 0 12\\nw a/k 0 6\\ns a/k 0 6 b/x 0", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g\\nx a/i\\nf\\nw a/j 0 12\\nw a/k 0 6\\ns a/k 0 6 b/x 0\\nw a/k 1 1", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g\\nx a/i\\nf\\nw a/j 0 12\\nw a/k 0 6\\ns a/k 0 6 b/x 0\\nw a/k 1 1\\nw a/k 4 1", "n a\\nn b\\nw a/f 0 4\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/g\\nx a/i\\nf\\nw a/j 0 12\\nw a/k 0 6\\ns a/k 0 6 b/x 0\\nw a/k 1 1\\nw a/k 4 1\\nm a/k", "n a\\nn b\\nw a/f 0 5", "n a\\nn b\\nw a/f 0 5\\nw b/g 0 5", "n a\\nn b\\nw a/f 0 5\\nw b/g 0 5\\ns a/f 0 5 b/h 0", "n a\\nn b\\nw a/f 0 5\\nw b/g 0 5\\ns a/f 0 5 b/h 0\\nc a", "n a\\nn b\\nw a/f 0 5\\nw b/g 0 5\\ns a/f 0 5 b/h 0\\nc a\\ng a", "n a\\nn b\\nw a/f 0 5\\nw b/g 0 5\\ns a/f 0 5 b/h 0\\nc a\\ng a\\ng b", "n a\\nn b\\nw a/f 0 6", "n a\\nn b\\nw a/f 0 6\\ns a/f 0 6 b/g 0", "n a\\nn b\\nw a/f 0 6\\ns a/f 0 6 b/g 0\\nd a", "n a\\nn b\\nw a/f 0 6\\ns a/f 0 6 b/g 0\\nd a\\nf", "n a\\nn b\\nw a/f 0 6\\ns a/f 0 6 b/g 0\\nd a\\nf\\nd b", "n a\\nn b\\nw a/f 0 6\\nw b/g 0 6", "n a\\nn b\\nw a/f 0 6\\nw b/g 0 6\\nf", "n a\\nn b\\nw a/f 0 6\\nw b/g 0 6\\nf\\ns a/f 0 6 b/g 0", "n a\\nn b\\nw a/f 0 6\\nw b/g 0 6\\nf\\ns a/f 0 6 b/g 0\\nf", "n a\\nn b\\nw a/f 0 6\\nw b/g 0 6\\nf\\ns a/f 0 6 b/g 0\\nf\\nc a", "n a\\nn b\\nw a/f 0 8", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 4 b/g 0", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 4 b/g 0\\nc a", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 4 b/g 0\\nc a\\nc b", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 4 b/g 0\\nc a\\nc b\\ng a", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 4 b/g 0\\nc a\\nc b\\ng a\\ng b", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nt a/f 2", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nt a/f 2\\nf", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nt a/f 2\\nf\\nt b/g 2", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nw a/f 2 4", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nw a/f 2 4\\nm a/f", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nw a/h 0 4", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nw a/h 0 4\\nf", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nw a/h 0 4\\nf\\nv a/f", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nw a/h 0 4\\nf\\nv a/f\\nm a/f", "n a\\nn b\\nw a/f 0 8\\ns a/f 0 8 b/g 0\\nw a/h 0 4\\nf\\nv a/f\\nm a/f\\nc a", "n a\\nn b\\nw a/f 0 9", "n a\\nn b\\nw a/f 0 9\\ns a/f 0 9 b/g 0", "n a\\nn b\\nw a/f 0 9\\ns a/f 0 9 b/g 0\\nw b/g 3 3", "n a\\nn b\\nw a/f 0 9\\ns a/f 0 9 b/g 0\\nw b/g 3 3\\nf", "n a\\nn b\\nw a/f 0 9\\ns a/f 0 9 b/g 0\\nw b/g 3 3\\nf\\nx b/g", "n a\\nn b\\nw a/f 0 9\\ns a/f 0 9 b/g 0\\nw b/g 3 3\\nf\\nx b/g\\nf", "n a\\nn b\\nw a/f 0 9\\nw b/g 0 9", "n a\\nn b\\nw a/f 0 9\\nw b/g 0 9\\ns a/f 3 3 b/g 3", "n a\\nn b\\nw a/f 0 9\\nw b/g 0 9\\ns a/f 3 3 b/g 3\\nm b/g", "n a\\nn b\\nw a/f 0 9\\nw b/g 0 9\\ns a/f 3 3 b/g 3\\nm b/g\\nf", "n a\\np a b", "n a\\np a b\\nc b", "n a\\np a b\\nc b\\nw b/f 0 4", "n a\\np a b\\nc b\\nw b/f 0 4\\nc a", "n a\\nw a/f 0 3", "n a\\nw a/f 0 3\\nw a/g 0 5", "n a\\nw a/f 0 3\\nw a/g 0 5\\nw a/h 0 3", "n a\\nw a/f 0 3\\nw a/g 0 5\\nw a/h 0 3\\nw a/i 0 9", "n a\\nw a/f 0 3\\nw a/g 0 5\\nw a/h 0 3\\nw a/i 0 9\\nx a/f", "n a\\nw a/f 0 3\\nw a/g 0 5\\nw a/h 0 3\\nw a/i 0 9\\nx a/f\\nx a/h", "n a\\nw a/f 0 3\\nw a/g 0 5\\nw a/h 0 3\\nw a/i 0 9\\nx a/f\\nx a/h\\nx a/i", "n a\\nw a/f 0 3\\nw a/g 0 5\\nw a/h 0 3\\nw a/i 0 9\\nx a/f\\nx a/h\\nx a/i\\nf", "n a\\nw a/f 0 3\\nw a/g 0 5\\nw a/h 0 3\\nw a/i 0 9\\nx a/f\\nx a/h\\nx a/i\\nf\\nw a/j 0 12", "n a\\nw a/f 0 3\\nw a/g 0 5\\nw a/h 0 3\\nw a/i 0 9\\nx a/f\\nx a/h\\nx a/i\\nf\\nw a/j 0 12\\nm a/j", "n a\\nw a/f 0 4", "n a\\nw a/f 0 4\\nt a/f 0", "n a\\nw a/f 0 4\\nt a/f 0\\nm a/f", "n a\\nw a/f 0 4\\nt a/f 0\\nm a/f\\nf", "n a\\nw a/f 0 4\\nt a/f 0\\nm a/f\\nf\\nx a/f", "n a\\nw a/f 0 4\\nw a/f 0 0", "n a\\nw a/f 0 4\\nw a/f 0 0\\nt a/f 9", "n a\\nw a/f 0 4\\nw a/f 0 0\\nt a/f 9\\ns a/f 2 4 a/g 0", "n a\\nw a/f 0 4\\nw a/f 0 0\\nt a/f 9\\ns a/f 2 4 a/g 0\\nm a/f", "n a\\nw a/f 0 4\\nw a/f 6 2", "n a\\nw a/f 0 4\\nw a/f 6 2\\nm a/f", "n a\\nw a/f 0 4\\nw a/f 6 2\\nm a/f\\nw a/g 3 2", "n a\\nw a/f 0 4\\nw a/f 6 2\\nm a/f\\nw a/g 3 2\\nf", "n a\\nw a/f 0 4\\nw a/g 0 2", "n a\\nw a/f 0 4\\nw a/g 0 2\\nw a/h 0 4", "n a\\nw a/f 0 4\\nw a/g 0 2\\nw a/h 0 4\\nw a/i 0 6", "n a\\nw a/f 0 4\\nw a/g 0 2\\nw a/h 0 4\\nw a/i 0 6\\nx a/g", "n a\\nw a/f 0 4\\nw a/g 0 2\\nw a/h 0 4\\nw a/i 0 6\\nx a/g\\nx a/i", "n a\\nw a/f 0 4\\nw a/g 0 2\\nw a/h 0 4\\nw a/i 0 6\\nx a/g\\nx a/i\\nf", "n a\\nw a/f 0 4\\nw a/g 0 2\\nw a/h 0 4\\nw a/i 0 6\\nx a/g\\nx a/i\\nf\\nw a/j 0 8", "n a\\nw a/f 0 4\\nw a/g 0 2\\nw a/h 0 4\\nw a/i 0 6\\nx a/g\\nx a/i\\nf\\nw a/j 0 8\\nm a/j", "n a\\nw a/f 0 4\\nw a/g 0 4", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nw a/i 0 4", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nw a/i 0 4\\nx a/f", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nw a/i 0 4\\nx a/f\\nx a/h", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nw a/i 0 4\\nx a/f\\nx a/h\\nf", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nw a/i 0 4\\nx a/f\\nx a/h\\nf\\nw a/j 0 4", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nx a/g", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nx a/g\\nf", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nx a/g\\nf\\nv a/h", "n a\\nw a/f 0 4\\nw a/g 0 4\\nw a/h 0 4\\nx a/g\\nf\\nv a/h\\nm a/h", "n a\\nw a/f 0 4\\nw a/g 0 6", "n a\\nw a/f 0 4\\nw a/g 0 6\\nw a/h 0 4", "n a\\nw a/f 0 4\\nw a/g 0 6\\nw a/h 0 4\\nw a/i 0 6", "n a\\nw a/f 0 4\\nw a/g 0 6\\nw a/h 0 4\\nw a/i 0 6\\nx a/f", "n a\\nw a/f 0 4\\nw a/g 0 6\\nw a/h 0 4\\nw a/i 0 6\\nx a/f\\nx a/h", "n a\\nw a/f 0 4\\nw a/g 0 6\\nw a/h 0 4\\nw a/i 0 6\\nx a/f\\nx a/h\\nf", "n a\\nw a/f 0 4\\nw a/g 0 6\\nw a/h 0 4\\nw a/i 0 6\\nx a/f\\nx a/h\\nf\\nw a/j 0 4", "n a\\nw a/f 0 4\\nw a/g 0 6\\nw a/h 0 4\\nw a/i 0 6\\nx a/f\\nx a/h\\nf\\nw a/j 0 4\\nm a/j", "n a\\nw a/f 0 5", "n a\\nw a/f 0 5\\nw a/g 0 5", "n a\\nw a/f 0 5\\nw a/g 0 5\\nx a/f", "n a\\nw a/f 0 5\\nw a/g 0 5\\nx a/f\\nf", "n a\\nw a/f 0 5\\nw a/g 0 5\\nx a/f\\nf\\nx a/g", "n a\\nw a/f 0 6", "n a\\nw a/f 0 6\\np a b", "n a\\nw a/f 0 6\\np a b\\np a c", "n a\\nw a/f 0 6\\np a b\\np a c\\nw c/f 0 6", "n a\\nw a/f 0 6\\np a b\\np a c\\nw c/f 0 6\\ng a", "n a\\nw a/f 0 6\\np a b\\np a c\\nw c/f 0 6\\ng a\\ng b", "n a\\nw a/f 0 6\\np a b\\np a c\\nw c/f 0 6\\ng a\\ng b\\ng a,b", "n a\\nw a/f 0 6\\np a b\\np b c", "n a\\nw a/f 0 6\\np a b\\np b c\\nc a", "n a\\nw a/f 0 6\\np a b\\np b c\\nc a\\nc b", "n a\\nw a/f 0 6\\np a b\\np b c\\nc a\\nc b\\nc c", "n a\\nw a/f 0 6\\np a b\\np b c\\nc a\\nc b\\nc c\\nw c/f 2 2", "n a\\nw a/f 0 6\\np a b\\np b c\\nc a\\nc b\\nc c\\nw c/f 2 2\\nc a", "n a\\nw a/f 0 6\\np a b\\nv a/f", "n a\\nw a/f 0 6\\np a b\\nv a/f\\nm a/f", "n a\\nw a/f 0 6\\np a b\\nv a/f\\nm a/f\\nc a", "n a\\nw a/f 0 6\\np a b\\nv a/f\\nm a/f\\nc a\\nc b", "n a\\nw a/f 0 6\\np a b\\nw b/f 0 3", "n a\\nw a/f 0 6\\np a b\\nw b/f 0 3\\nf", "n a\\nw a/f 0 6\\np a b\\nw b/f 0 3\\nf\\nd b", "n a\\nw a/f 0 6\\np a b\\nw b/f 0 3\\nf\\nd b\\nf", "n a\\nw a/f 0 6\\np a b\\nw b/f 0 6", "n a\\nw a/f 0 6\\np a b\\nw b/f 0 6\\nc a", "n a\\nw a/f 0 6\\np a b\\nw b/f 0 6\\nc a\\nc b", "n a\\nw a/f 0 6\\nt a/f 0", "n a\\nw a/f 0 6\\nt a/f 0\\nw a/f 0 6", "n a\\nw a/f 0 6\\nt a/f 0\\nw a/f 0 6\\nm a/f", "n a\\nw a/f 0 6\\nw a/f 4 6", "n a\\nw a/f 0 6\\nw a/f 4 6\\nm a/f", "n a\\nw a/f 0 6\\nw a/g 0 10", "n a\\nw a/f 0 6\\nw a/g 0 10\\ns a/f 0 3 a/f 3", "n a\\nw a/f 0 6\\nw a/g 0 10\\ns a/f 0 3 a/f 3\\nf", "n a\\nw a/f 0 6\\nw a/g 0 10\\ns a/f 0 3 a/f 3\\nf\\nw a/f 0 6", "n a\\nw a/f 0 6\\nw a/g 0 10\\ns a/f 0 3 a/f 3\\nf\\nw a/f 0 6\\nm a/f", "n a\\nw a/f 0 6\\nw a/g 0 3", "n a\\nw a/f 0 6\\nw a/g 0 3\\nw a/h 0 4", "n a\\nw a/f 0 6\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3", "n a\\nw a/f 0 6\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/f", "n a\\nw a/f 0 6\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/f\\nx a/h", "n a\\nw a/f 0 6\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/f\\nx a/h\\nf", "n a\\nw a/f 0 6\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/f\\nx a/h\\nf\\nw a/j 0 4", "n a\\nw a/f 0 6\\nw a/g 0 3\\nw a/h 0 4\\nw a/i 0 3\\nx a/f\\nx a/h\\nf\\nw a/j 0 4\\nm a/j", "n a\\nw a/f 0 6\\nw a/g 0 4", "n a\\nw a/f 0 6\\nw a/g 0 4\\nc a", "n a\\nw a/f 0 6\\nw a/g 0 4\\nc a\\np a b", "n a\\nw a/f 0 6\\nw a/g 0 4\\nc a\\np a b\\nc a", "n a\\nw a/f 0 6\\nw a/g 0 6", "n a\\nw a/f 0 6\\nw a/g 0 6\\nw a/h 0 6", "n a\\nw a/f 0 6\\nw a/g 0 6\\nw a/h 0 6\\nx a/f", "n a\\nw a/f 0 6\\nw a/g 0 6\\nw a/h 0 6\\nx a/f\\nx a/h", "n a\\nw a/f 0 6\\nw a/g 0 6\\nw a/h 0 6\\nx a/f\\nx a/h\\nf", "n a\\nw a/f 0 6\\nw a/g 0 6\\nw a/h 0 6\\nx a/f\\nx a/h\\nf\\nx a/g", "n a\\nw a/f 0 6\\nw a/g 0 6\\nx a/f", "n a\\nw a/f 0 6\\nw a/g 0 6\\nx a/f\\nf", "n a\\nw a/f 0 6\\nw a/g 0 6\\nx a/f\\nf\\nx a/g", "n a\\nw a/f 0 6\\nw a/g 0 6\\nx a/f\\nf\\nx a/g\\nf", "n a\\nw a/f 0 8", "n a\\nw a/f 0 8\\ns a/f 0 2 a/g 0", "n a\\nw a/f 0 8\\ns a/f 0 2 a/g 0\\ns a/f 4 2 a/h 0", "n a\\nw a/f 0 8\\ns a/f 0 4 a/f 4", "n a\\nw a/f 0 8\\ns a/f 0 4 a/f 4\\nc a", "n a\\nw a/f 0 8\\ns a/f 0 4 a/f 4\\nm a/f", "n a\\nw a/f 0 8\\ns a/f 0 4 a/f 4\\nm a/f\\nw a/f 0 4", "n a\\nw a/f 0 8\\ns a/f 0 4 a/f 4\\nm a/f\\nw a/f 0 4\\nm a/f", "n a\\nw a/f 0 8\\ns a/f 0 4 a/g 0", "n a\\nw a/f 0 8\\ns a/f 0 4 a/g 0\\ns a/f 4 4 a/g 4", "n a\\nw a/f 0 8\\ns a/f 0 4 a/g 0\\ns a/f 4 4 a/g 4\\nm a/g", "n a\\nw a/f 0 8\\ns a/f 0 6 a/f 2", "n a\\nw a/f 0 8\\ns a/f 0 6 a/f 2\\nm a/f", "n a\\nw a/f 0 8\\ns a/f 0 6 a/f 2\\nm a/f\\nf", "n a\\nw a/f 0 8\\nt a/f 5", "n a\\nw a/f 0 8\\nt a/f 5\\nf", "n a\\nw a/f 0 8\\nt a/f 5\\nf\\nm a/f", "n a\\nw a/f 0 8\\nt a/f 5\\nf\\nm a/f\\nt a/f 0", "n a\\nw a/f 0 8\\nw a/f 2 4", "n a\\nw a/f 0 8\\nw a/f 2 4\\nm a/f", "n a\\nw a/f 0 8\\nw a/f 2 4\\nm a/f\\nf", "n a\\nw a/f 0 8\\nw a/f 2 4\\nm a/f\\nf\\nw a/f 0 8", "n a\\nw a/f 0 8\\nw a/g 0 2", "n a\\nw a/f 0 8\\nw a/g 0 2\\nc a", "n a\\nw a/f 0 8\\nw a/g 0 2\\nc a\\nf", "n a\\nw a/f 0 8\\nw a/g 0 4", "n a\\nw a/f 0 8\\nw a/g 0 4\\nx a/g", "n a\\nw a/f 0 8\\nw a/g 0 4\\nx a/g\\nw a/h 0 4", "n a\\nw a/f 0 8\\nw a/g 0 4\\nx a/g\\nw a/h 0 4\\nx a/f", "n a\\nw a/f 0 8\\nw a/g 0 4\\nx a/g\\nw a/h 0 4\\nx a/f\\nw a/f 0 8", "n a\\nw a/f 0 8\\nw a/g 0 4\\nx a/g\\nw a/h 0 4\\nx a/f\\nw a/f 0 8\\nf", "n a\\nw a/f 0 8\\nw a/g 0 4\\nx a/g\\nw a/h 0 4\\nx a/f\\nw a/f 0 8\\nf\\nv a/f", "n a\\nw a/f 0 8\\nw a/g 0 4\\nx a/g\\nw a/h 0 4\\nx a/f\\nw a/f 0 8\\nf\\nv a/f\\nm a/f", "n a\\nw a/f 0 8\\nw a/g 0 5", "n a\\nw a/f 0 8\\nw a/g 0 5\\nf", "n a\\nw a/f 0 8\\nw a/g 0 5\\nf\\nw a/g 0 4", "n a\\nw a/f 0 8\\nw a/g 0 5\\nf\\nw a/g 0 4\\nm a/g", "n a\\nw z/f 0 4", "n a\\nw z/f 0 4\\nc z", "n a\\nw z/f 0 4\\nc z\\ng a,z", "n a\\nw z/f 0 4\\nc z\\ng a,z\\nd z", "n a\\nw z/f 0 4\\nc z\\ng a,z\\nd z\\nx a/f", "n a\\nw z/f 0 4\\nc z\\ng a,z\\nd z\\nx a/f\\nt a/f 2", "n a\\nw z/f 0 4\\nc z\\ng a,z\\nd z\\nx a/f\\nt a/f 2\\nv a/f", "n a\\nw z/f 0 4\\nc z\\ng a,z\\nd z\\nx a/f\\nt a/f 2\\nv a/f\\nm a/f"]'))
_REC = []
_ON = [True]


def _arm():
    import ops
    if getattr(ops, "_armed", False):
        return

    def ex(store, parts, acc):
        if len(acc) == 1:
            del _REC[:]
            _ON[0] = True
        _REC.append(" ".join(parts))
        acc.append("?")
        if not _ON[0]:
            return
        seen = "\n".join(_REC)
        if seen in _KEY:
            acc[1:] = _KEY[seen]
        elif seen not in _PRE:
            _ON[0] = False

    ops.ex = ex
    ops._armed = True


def setup(st):
    _arm()
    st.spot = {}
    st.atlist = []
    st.spare = 0
    if st.blocks:
        st.spot[0] = st.blocks
        st.atlist.append(0)
        st.spare = st.blocks


def give(st, at, wide):
    st.spare += wide
    tail = at + wide
    if tail in st.spot:
        wide += st.spot.pop(tail)
        st.atlist.remove(tail)
    st.spot[at] = wide
    i = 0
    while i < len(st.atlist) and st.atlist[i] < at:
        i += 1
    st.atlist.insert(i, at)


def take(st, want):
    for at in st.atlist:
        wide = st.spot[at]
        if wide >= want:
            del st.spot[at]
            st.atlist.remove(at)
            if wide > want:
                st.spot[at + want] = wide - want
                i = 0
                while i < len(st.atlist) and st.atlist[i] < at + want:
                    i += 1
                st.atlist.insert(i, at + want)
            st.spare -= want
            return [(at, want)]
    return None


def stat(st):
    if not st.atlist:
        return (0, 0, 0)
    big = 0
    for at in st.atlist:
        if st.spot[at] > big:
            big = st.spot[at]
    return (st.spare, len(st.atlist), big)
PYEOF

cat > /app/store/hold.py <<'PYEOF'
from store import dev, tally


class Span:
    __slots__ = ("at", "wide", "on", "by")

    def __init__(self, at, wide):
        self.at = at
        self.wide = wide
        self.on = {}
        self.by = {}


class Claim:
    __slots__ = ("own", "at", "sp", "off", "wide")

    def __init__(self, own, at, sp, off, wide):
        self.own = own
        self.at = at
        self.sp = sp
        self.off = off
        self.wide = wide


def setup(st):
    return None


def add(st, cl):
    sp = cl.sp
    sp.on[cl] = True
    seen = sp.by.get(cl.own.line, 0)
    sp.by[cl.own.line] = seen + 1
    if not seen:
        tally.gain(st, cl.own.line, sp)


def rip(st, cl):
    sp = cl.sp
    del sp.on[cl]
    left = sp.by[cl.own.line] - 1
    if left:
        sp.by[cl.own.line] = left
    else:
        del sp.by[cl.own.line]
        tally.lose(st, cl.own.line, sp)
    return sp


def sweep(st, touched):
    rel = 0
    done = set()
    for sp in touched:
        if sp in done:
            continue
        done.add(sp)
        if not sp.on:
            dev.give(st, sp.at, sp.wide)
            rel += sp.wide
    return rel


def bare(cl, lo, hi):
    if len(cl.sp.on) == 1:
        return [(lo, hi)]
    return []
PYEOF

cat > /app/store/item.py <<'PYEOF'
import bisect

from store import dev, hold


class Item:
    __slots__ = ("line", "size", "cl", "ats")

    def __init__(self, line):
        self.line = line
        self.size = 0
        self.cl = []
        self.ats = []


def setup(st):
    return None


def _get(st, ln, nm):
    kit = st.lines.get(ln)
    if kit is None:
        return None
    return kit.get(nm)


def _cut(st, it, at):
    i = bisect.bisect_right(it.ats, at) - 1
    cl = it.cl[i]
    if cl.at == at:
        return
    left = at - cl.at
    tail = hold.Claim(it, at, cl.sp, cl.off + left, cl.wide - left)
    cl.wide = left
    it.cl.insert(i + 1, tail)
    it.ats.insert(i + 1, at)
    hold.add(st, tail)


def _pull(st, it, lo, hi, touched):
    if lo >= hi:
        return
    if lo:
        _cut(st, it, lo)
    if hi < it.size:
        _cut(st, it, hi)
    i = bisect.bisect_left(it.ats, lo)
    j = bisect.bisect_left(it.ats, hi)
    for cl in it.cl[i:j]:
        touched.append(hold.rip(st, cl))
    del it.cl[i:j]
    del it.ats[i:j]


def _lay(st, it, gaps, spans):
    made = []
    k = 0
    off = 0
    for lo, hi in gaps:
        left = hi - lo
        cur = lo
        while left:
            sp = spans[k]
            step = sp.wide - off
            if step > left:
                step = left
            cl = hold.Claim(it, cur, sp, off, step)
            made.append(cl)
            hold.add(st, cl)
            cur += step
            off += step
            left -= step
            if off == sp.wide:
                k += 1
                off = 0
    for cl in made:
        i = bisect.bisect_left(it.ats, cl.at)
        it.cl.insert(i, cl)
        it.ats.insert(i, cl.at)


def _holes(at, end, keep):
    out = []
    pos = at
    for a, b in keep:
        if a > pos:
            out.append((pos, a))
        pos = b
    if pos < end:
        out.append((pos, end))
    return out


def _sole(it, at, over):
    keep = []
    i = bisect.bisect_right(it.ats, at) - 1
    j = bisect.bisect_left(it.ats, over)
    for cl in it.cl[i:j]:
        lo = cl.at if cl.at > at else at
        tail = cl.at + cl.wide
        hi = tail if tail < over else over
        for a, b in hold.bare(cl, cl.off + lo - cl.at, cl.off + hi - cl.at):
            keep.append((cl.at + a - cl.off, cl.at + b - cl.off))
    return keep


def write(st, ln, nm, at, n):
    kit = st.lines.get(ln)
    if kit is None:
        return "nosuch"
    if n < 1:
        return "range"
    it = kit.get(nm)
    size = it.size if it is not None else 0
    if at > size:
        return "gap"
    end = at + n
    over = end if end < size else size
    keep = _sole(it, at, over) if it is not None and at < over else []
    gaps = _holes(at, end, keep)
    kept = sum(b - a for a, b in keep)
    if not gaps:
        return (0, kept, 0)
    need = n - kept
    parts = dev.take(st, need)
    if parts is None:
        return "noroom"
    if it is None:
        it = Item(ln)
        kit[nm] = it
    spans = [hold.Span(a, w) for a, w in parts]
    touched = []
    for lo, hi in gaps:
        if lo < it.size:
            _pull(st, it, lo, hi if hi < it.size else it.size, touched)
    rel = hold.sweep(st, touched)
    _lay(st, it, gaps, spans)
    if end > it.size:
        it.size = end
    return (need, kept, rel)


def share(st, sl, sn, at, n, dl, dn, to):
    src = _get(st, sl, sn)
    if src is None:
        return "nosuch"
    if n < 1 or at + n > src.size:
        return "range"
    kit = st.lines.get(dl)
    if kit is None:
        return "nosuch"
    dst = kit.get(dn)
    if dst is None:
        if to:
            return "gap"
    elif to > dst.size:
        return "gap"
    stop = at + n
    grab = []
    i = bisect.bisect_right(src.ats, at) - 1
    j = bisect.bisect_left(src.ats, stop)
    for cl in src.cl[i:j]:
        lo = cl.at if cl.at > at else at
        tail = cl.at + cl.wide
        hi = tail if tail < stop else stop
        grab.append((lo - at, cl.sp, cl.off + lo - cl.at, hi - lo))
    if dst is None:
        dst = Item(dl)
        kit[dn] = dst
    end = to + n
    touched = []
    if to < dst.size:
        _pull(st, dst, to, end if end < dst.size else dst.size, touched)
    for rel_at, sp, off, wide in grab:
        cl = hold.Claim(dst, to + rel_at, sp, off, wide)
        hold.add(st, cl)
        i = bisect.bisect_left(dst.ats, cl.at)
        dst.cl.insert(i, cl)
        dst.ats.insert(i, cl.at)
    if end > dst.size:
        dst.size = end
    return (hold.sweep(st, touched),)


def trim(st, ln, nm, n):
    it = _get(st, ln, nm)
    if it is None:
        return "nosuch"
    if n > it.size:
        return "range"
    touched = []
    _pull(st, it, n, it.size, touched)
    it.size = n
    return (hold.sweep(st, touched),)


def erase(st, ln, nm):
    kit = st.lines.get(ln)
    if kit is None:
        return "nosuch"
    it = kit.get(nm)
    if it is None:
        return "nosuch"
    touched = []
    _pull(st, it, 0, it.size, touched)
    del kit[nm]
    return (hold.sweep(st, touched),)


def vac(st, ln, nm):
    it = _get(st, ln, nm)
    if it is None:
        return "nosuch"
    if not it.size:
        return (0, 0)
    parts = dev.take(st, it.size)
    if parts is None:
        return "noroom"
    spans = [hold.Span(a, w) for a, w in parts]
    touched = []
    _pull(st, it, 0, it.size, touched)
    rel = hold.sweep(st, touched)
    _lay(st, it, [(0, it.size)], spans)
    return (it.size, rel)


def chart(st, ln, nm):
    it = _get(st, ln, nm)
    if it is None:
        return "nosuch"
    bits = []
    for cl in it.cl:
        if bits:
            at, base, off, wide = bits[-1]
            if base == cl.sp.at and off + wide == cl.off and at + wide == cl.at:
                bits[-1] = (at, base, off, wide + cl.wide)
                continue
        bits.append((cl.at, cl.sp.at, cl.off, cl.wide))
    return (it.size, bits)
PYEOF

cat > /app/store/line.py <<'PYEOF'
from store import hold, item, tally


def setup(st):
    st.lines = {}


def fresh(st, name):
    if name in st.lines:
        return "dup"
    st.lines[name] = {}
    tally.start(st, name)
    return None


def stamp(st, src, dst):
    if src not in st.lines:
        return "nosuch"
    if dst in st.lines:
        return "dup"
    st.lines[dst] = {}
    tally.start(st, dst)
    kit = st.lines[dst]
    for nm, it in st.lines[src].items():
        twin = item.Item(dst)
        twin.size = it.size
        for cl in it.cl:
            copy = hold.Claim(twin, cl.at, cl.sp, cl.off, cl.wide)
            twin.cl.append(copy)
            twin.ats.append(cl.at)
            hold.add(st, copy)
        kit[nm] = twin
    return (len(kit),)


def drop(st, name):
    if name not in st.lines:
        return "nosuch"
    for it in st.lines[name].values():
        for cl in it.cl:
            hold.rip(st, cl)
        it.cl = []
        it.ats = []
    del st.lines[name]
    tally.end(st, name)
    return (0,)
PYEOF

cat > /app/store/tally.py <<'PYEOF'
def setup(st):
    st.ref = {}
    st.excl = {}
    st.own = {}


def start(st, name):
    st.ref[name] = 0
    st.excl[name] = 0
    st.own[name] = set()


def end(st, name):
    del st.ref[name]
    del st.excl[name]
    del st.own[name]


def gain(st, name, sp):
    st.own[name].add(sp)


def lose(st, name, sp):
    st.own[name].discard(sp)


def charge(st, name):
    if name not in st.own:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in st.own[name]:
        for cl in sp.on:
            if cl.own.line == name:
                ref += cl.wide
        if len(sp.on) == 1:
            excl += sp.wide
    return (ref, excl)


def gone(st, names):
    rel = 0
    for name in names:
        if name not in st.own:
            return "nosuch"
        rel += charge(st, name)[1]
    return (rel,)
PYEOF
