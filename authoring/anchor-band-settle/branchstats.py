#!/usr/bin/env python3
"""Per family, how often each branch of the contract fires. Never ships.

    python3 branchstats.py [per] [seed]
"""
import collections
import sys

import lab

cases, gen, _model = lab.sealed()
KEYS = ['settled in pass 1', 'settled in pass 2', 'settled in pass 3', 'settled in pass 4',
        'four passes, no settle', 'holder changed mid-loop', 'fallback used', 'clamped pass',
        'none before', 'none in pass 1', 'off scroll', 'off live']


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 20
    seed = argv[2] if len(argv) > 2 else 'stats'
    nv = lab.naive()
    by = collections.defaultdict(dict)
    frames = collections.Counter()
    for fam, name, lines in gen.programs(seed, per, small_only=True):
        nv.STATS = by[fam]
        frames[fam] += len(nv.run('\n'.join(lines) + '\n'))
    nv.STATS = None
    print('%-7s %6s ' % ('fam', 'frames') + ' '.join('%7s' % k.split()[-1][:7] for k in KEYS))
    print('%-7s %6s ' % ('', '') + ' '.join('%7s' % k.split()[0][:7] for k in KEYS))
    for fam, _big in gen.FAMILIES:
        if fam in by:
            st = by[fam]
            print('%-7s %6d ' % (fam, frames[fam]) + ' '.join(
                '%6.1f%%' % (100.0 * st.get(k, 0) / frames[fam]) for k in KEYS))


if __name__ == '__main__':
    main(sys.argv)
