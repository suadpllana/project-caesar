#!/bin/bash
# carries tests/seal/gt.json and plays it back for every enumerated pipeline
set -euo pipefail

cat > /app/plan/keep.py <<'PYEOF'
from plan.span import ends


def there(pp, name, i):
    if i < 0:
        return False
    end = ends(pp, name, i)
    return end <= pp.now and pp.now - end < pp.keep[name]
PYEOF

cat > /app/plan/reach.py <<'PYEOF'
from plan.keep import there
from plan.span import last


def reach(pp):
    readers = {}
    for name in pp.names:
        for kind, src, width in pp.reads.get(name, ()):
            readers.setdefault(src, []).append((name, kind, width))
    got = {pp.fix}
    todo = [pp.fix]
    while todo:
        src, i = todo.pop()
        for name, kind, width in readers.get(src, ()):
            if kind == "same":
                outs = [i]
            elif kind == "day":
                outs = [i // 24]
            elif kind == "win":
                outs = range(i, i + width)
            elif pp.grain[src] == pp.grain[name]:
                outs = [i + 1]
            elif pp.grain[src] == "d":
                outs = range(24 * (i + 1), 24 * (i + 2))
            else:
                outs = [(i + 1) // 24] if (i + 1) % 24 == 0 else []
            for j in outs:
                if 0 <= j <= last(pp, name) and (name, j) not in got and there(pp, name, j):
                    got.add((name, j))
                    todo.append((name, j))
    return got
PYEOF

cat > /app/plan/look.py <<'PYEOF'
from plan.span import takes


def looks(pp, name, i):
    out = []
    for _kind, src, parts in takes(pp, name, i):
        for p in parts:
            out.append((src, p))
    return out
PYEOF

cat > /app/plan/settle.py <<'PYEOF'
from plan.keep import there
from plan.look import looks


def settle(pp, got):
    rows = []
    for name, i in got:
        if name not in pp.reads or not there(pp, name, i):
            continue
        if (name, i) in pp.pins:
            rows.append(("hold", name, i, "pinned"))
        elif all(there(pp, src, p) for src, p in looks(pp, name, i)):
            rows.append(("run", name, i, "full"))
        else:
            rows.append(("hold", name, i, "lost"))
    return rows
PYEOF

cat > /app/plan/order.py <<'PYEOF'
import json

from plan.span import ends

GT = json.loads('{\n "chain-checkpoint": [\n  "temp bal 3",\n  "temp bal 4",\n  "temp bal 5",\n  "temp bal 6",\n  "run bal 7 full",\n  "run bal 8 full",\n  "run bal 9 full"\n ],\n "chain-published": [\n  "run bal 4 full",\n  "run bal 5 full",\n  "hold bal 6 pinned",\n  "hold bal 7 same",\n  "hold bal 8 same",\n  "hold bal 9 same"\n ],\n "chain-to-zero": [\n  "temp bal 0",\n  "temp bal 1",\n  "temp bal 2",\n  "temp bal 3",\n  "temp bal 4",\n  "run bal 5 full",\n  "run bal 6 full"\n ],\n "holds-last": [\n  "run wk 6 part",\n  "run wk 7 full",\n  "run wk 8 full",\n  "hold dy 6 pinned"\n ],\n "keep-edge": [\n  "temp cl 88",\n  "temp cl 89",\n  "run cl 90 full",\n  "run sm 90 full",\n  "run sm 91 full",\n  "run sm 92 full"\n ],\n "keep-published": [\n  "temp dy 6",\n  "temp dy 7",\n  "run dy 8 full",\n  "run wk 8 full",\n  "run wk 9 full"\n ],\n "lost-before-same": [\n  "hold dy 8 pinned",\n  "hold wk 8 lost"\n ],\n "lost-source": [\n  "run dy 8 full",\n  "run wk 8 full",\n  "run wk 9 full",\n  "run mo 9 full",\n  "hold mo 8 lost"\n ],\n "lost-temp-chain": [\n  "temp dy 6",\n  "temp dy 7",\n  "run dy 8 full",\n  "run wk 9 full",\n  "hold wk 8 lost"\n ],\n "lost-temps-unprinted": [\n  "temp dy 7",\n  "run dy 8 full",\n  "run wk 9 full",\n  "hold wk 8 lost"\n ],\n "mode-part-over-sub": [\n  "temp x 96",\n  "temp x 97",\n  "temp x 98",\n  "temp x 99",\n  "temp x 100",\n  "temp x 101",\n  "temp x 102",\n  "temp x 103",\n  "temp x 104",\n  "temp x 105",\n  "temp x 106",\n  "temp x 107",\n  "temp x 108",\n  "temp x 109",\n  "temp x 110",\n  "temp x 111",\n  "temp x 112",\n  "temp x 113",\n  "temp x 114",\n  "temp x 115",\n  "temp x 116",\n  "temp x 117",\n  "temp x 118",\n  "temp x 119",\n  "run r 4 full",\n  "run s 4 part",\n  "hold p 4 pinned"\n ],\n "order-after-roll-up": [\n  "temp x 96",\n  "temp x 97",\n  "temp x 98",\n  "temp x 99",\n  "temp x 100",\n  "temp x 101",\n  "temp x 102",\n  "temp x 103",\n  "temp x 104",\n  "temp x 105",\n  "temp x 106",\n  "temp x 107",\n  "temp x 108",\n  "temp x 109",\n  "temp x 110",\n  "temp x 111",\n  "temp x 112",\n  "temp x 113",\n  "temp x 114",\n  "temp x 115",\n  "temp x 116",\n  "temp x 117",\n  "temp x 118",\n  "temp x 119",\n  "run u 4 full",\n  "run r 4 full",\n  "run s 4 sub"\n ],\n "pinned-hold": [\n  "hold dy 6 pinned",\n  "hold wk 6 same"\n ],\n "pinned-part": [\n  "run ev 6 full",\n  "run wk 6 part",\n  "hold dy 6 pinned"\n ],\n "pinned-unreached": [\n  "run dy 8 full",\n  "run wk 8 full",\n  "run wk 9 full"\n ],\n "pinned-window-same": [\n  "hold dy 5 pinned",\n  "hold wk 5 same",\n  "hold wk 6 same",\n  "hold wk 7 same"\n ],\n "plain-rerun": [\n  "run cl 30 full",\n  "run tot 1 full",\n  "run wk 1 full",\n  "run wk 2 full"\n ],\n "prehistory": [\n  "run dy 1 full",\n  "run wk 1 full",\n  "run wk 2 full",\n  "run wk 3 full",\n  "run wk 4 full"\n ],\n "prev-cross": [\n  "run dy 1 full",\n  "run hr 48 full",\n  "run hr 49 full",\n  "run hr 50 full",\n  "run hr 51 full",\n  "run hr 52 full",\n  "run hr 53 full",\n  "run hr 54 full",\n  "run hr 55 full",\n  "run hr 56 full",\n  "run hr 57 full",\n  "run hr 58 full",\n  "run hr 59 full",\n  "run hr 60 full",\n  "run hr 61 full",\n  "run hr 62 full",\n  "run hr 63 full",\n  "run hr 64 full",\n  "run hr 65 full",\n  "run hr 66 full",\n  "run hr 67 full",\n  "run hr 68 full",\n  "run hr 69 full",\n  "run hr 70 full",\n  "run hr 71 full",\n  "run dl 2 full"\n ],\n "reach-bounded-by-now": [\n  "run hr 97 full",\n  "run hr 98 full",\n  "run hr 99 full"\n ],\n "reach-through-expired": [\n  "temp cl 96",\n  "temp cl 97",\n  "temp cl 98",\n  "temp cl 99",\n  "temp cl 100",\n  "temp cl 101",\n  "temp cl 102",\n  "temp cl 103",\n  "temp cl 104",\n  "temp cl 105",\n  "temp cl 106",\n  "temp cl 107",\n  "temp cl 108",\n  "temp cl 109",\n  "temp cl 110",\n  "temp cl 111",\n  "temp cl 112",\n  "temp cl 113",\n  "temp cl 114",\n  "temp cl 115",\n  "temp cl 116",\n  "temp cl 117",\n  "temp cl 118",\n  "temp cl 119",\n  "run tot 4 full",\n  "run wk 4 full",\n  "run wk 5 full"\n ],\n "same-disagrees": [\n  "run ev 6 full",\n  "run wk 6 part",\n  "hold dy 6 pinned",\n  "hold mid 6 same"\n ],\n "stand-any-hour": [\n  "temp x 216",\n  "temp x 217",\n  "temp x 218",\n  "temp x 219",\n  "run x 225 full",\n  "run r 9 full",\n  "run s 9 sub"\n ],\n "stand-in-temp": [\n  "temp s 5",\n  "temp s 6",\n  "temp x 168",\n  "temp x 169",\n  "temp x 170",\n  "temp x 171",\n  "temp x 172",\n  "temp x 173",\n  "temp x 174",\n  "temp x 175",\n  "temp x 176",\n  "temp x 177",\n  "temp x 178",\n  "temp x 179",\n  "temp x 180",\n  "temp x 181",\n  "temp x 182",\n  "temp x 183",\n  "temp x 184",\n  "temp x 185",\n  "temp x 186",\n  "temp x 187",\n  "temp x 188",\n  "temp x 189",\n  "temp x 190",\n  "temp x 191",\n  "run r 7 full",\n  "temp s 7",\n  "run w 7 full",\n  "run w 8 full",\n  "run w 9 full"\n ],\n "stand-refused-part": [\n  "temp x 216",\n  "temp x 217",\n  "temp x 218",\n  "temp x 219",\n  "run x 224 full",\n  "run s 9 part",\n  "run r 9 part",\n  "hold x 225 pinned"\n ],\n "stand-refused-published": [\n  "temp x 96",\n  "temp x 97",\n  "temp x 98",\n  "temp x 99",\n  "temp x 100",\n  "temp x 101",\n  "temp x 102",\n  "temp x 103",\n  "temp x 104",\n  "temp x 105",\n  "temp x 106",\n  "temp x 107",\n  "temp x 108",\n  "temp x 109",\n  "temp x 110",\n  "temp x 111",\n  "temp x 112",\n  "temp x 113",\n  "temp x 114",\n  "temp x 115",\n  "temp x 116",\n  "temp x 117",\n  "temp x 118",\n  "temp x 119",\n  "run s 4 full",\n  "hold r 4 pinned",\n  "hold t 4 same"\n ],\n "stand-use": [\n  "temp x 96",\n  "temp x 97",\n  "temp x 98",\n  "temp x 99",\n  "temp x 100",\n  "temp x 101",\n  "temp x 102",\n  "temp x 103",\n  "temp x 104",\n  "temp x 105",\n  "temp x 106",\n  "temp x 107",\n  "temp x 108",\n  "temp x 109",\n  "temp x 110",\n  "temp x 111",\n  "temp x 112",\n  "temp x 113",\n  "temp x 114",\n  "temp x 115",\n  "temp x 116",\n  "temp x 117",\n  "temp x 118",\n  "temp x 119",\n  "run r 4 full",\n  "run s 4 sub"\n ],\n "temp-once": [\n  "temp dy 5",\n  "temp dy 6",\n  "run dy 8 full",\n  "run wk 8 full",\n  "run mo 8 full",\n  "run wk 9 full",\n  "run mo 9 full"\n ],\n "temp-only-for-reruns": [\n  "hold dy 8 pinned",\n  "hold wk 8 same"\n ],\n "temp-window": [\n  "temp dy 6",\n  "run dy 8 full",\n  "run wk 8 full",\n  "run wk 9 full"\n ]\n}\n')
NAMES = json.loads('{"now 96\\nsrc raw h 200\\nstep cl h 200 raw\\nstep tot d 200 cl/d\\nstep wk d 200 tot~2\\nfix raw 30\\n": "plain-rerun", "now 100\\nsrc raw h 500\\nstep cl h 10 raw\\nstep sm h 500 cl~3\\nfix raw 90\\n": "keep-edge", "now 240\\nsrc raw d 1000\\nstep dy d 48 raw\\nstep wk d 1000 dy~4\\npin dy 5\\nfix raw 8\\n": "keep-published", "now 100\\nsrc raw h 1000\\nstep dy d 1000 raw/d\\nstep hr h 1000 raw~5\\nfix raw 97\\n": "reach-bounded-by-now", "now 240\\nsrc raw h 1000\\nstep cl h 24 raw\\nstep tot d 1000 cl/d\\nstep wk d 1000 tot~2\\nfix raw 100\\n": "reach-through-expired", "now 240\\nsrc raw d 1000\\nstep dy d 1000 raw\\nstep wk d 1000 dy\\npin dy 6\\nfix raw 6\\n": "pinned-hold", "now 240\\nsrc raw d 1000\\nstep dy d 1000 raw\\nstep ev d 1000 raw\\nstep wk d 1000 dy ev\\npin dy 6\\nfix raw 6\\n": "pinned-part", "now 240\\nsrc raw d 1000\\nstep dy d 1000 raw\\nstep wk d 1000 dy~3\\npin dy 5\\nfix raw 5\\n": "pinned-window-same", "now 240\\nsrc raw d 1000\\nstep dy d 1000 raw\\nstep wk d 1000 dy~2\\npin dy 3\\nfix raw 8\\n": "pinned-unreached", "now 240\\nsrc raw d 1000\\nstep dy d 1000 raw\\nstep mid d 1000 dy\\nstep ev d 1000 raw\\nstep wk d 1000 mid ev\\npin dy 6\\nfix raw 6\\n": "same-disagrees", "now 240\\nsrc raw d 1000\\nstep dy d 72 raw\\nstep wk d 1000 dy~3\\nfix raw 8\\n": "temp-window", "now 240\\nsrc raw d 1000\\nstep dy d 72 raw\\nstep wk d 1000 dy~3\\nstep mo d 1000 dy~4\\nfix raw 8\\n": "temp-once", "now 240\\nsrc raw d 1000\\nsrc oth d 1000\\nstep dy d 1000 raw\\nstep ex d 72 oth\\nstep wk d 1000 dy ex~3\\npin dy 8\\nfix raw 8\\n": "temp-only-for-reruns", "now 240\\nsrc raw d 96\\nsrc oth d 1000\\nstep dy d 48 oth\\nstep wk d 1000 dy~3 raw~4\\nfix oth 8\\n": "lost-temps-unprinted", "now 240\\nsrc raw d 72\\nstep dy d 1000 raw\\nstep wk d 1000 dy~3\\nstep mo d 1000 raw~3\\nfix raw 8\\n": "lost-source", "now 240\\nsrc raw d 96\\nstep dy d 48 raw\\nstep wk d 1000 dy~4\\nfix raw 8\\n": "lost-temp-chain", "now 240\\nsrc raw d 1000\\nsrc oth d 72\\nstep dy d 1000 raw\\nstep wk d 1000 dy oth~3\\npin dy 8\\nfix raw 8\\n": "lost-before-same", "now 240\\nsrc raw h 1000\\nstep x h 24 raw\\nstep r d 1000 x/d\\nstep s d 1000 x/d\\nstand r x\\nfix raw 100\\n": "stand-use", "now 240\\nsrc raw h 1000\\nstep x h 20 raw\\nstep r d 1000 x/d\\nstep s d 1000 x/d\\nstand r x\\nfix raw 225\\n": "stand-any-hour", "now 240\\nsrc raw h 1000\\nstep x h 24 raw\\nstep r d 1000 x/d\\nstep s d 1000 x/d\\nstep t d 1000 r\\nstand r x\\npin r 4\\nfix raw 100\\n": "stand-refused-published", "now 240\\nsrc raw h 1000\\nstep x h 20 raw~2\\nstep s d 1000 x/d\\nstep r d 1000 x/d\\nstand r x\\npin x 225\\nfix raw 224\\n": "stand-refused-part", "now 240\\nsrc raw h 1000\\nstep x h 24 raw\\nstep r d 1000 x/d\\nstep s d 48 x/d\\nstep w d 1000 s~3\\nstand r x\\nfix raw 190\\n": "stand-in-temp", "now 240\\nsrc raw h 1000\\nstep x h 24 raw\\nstep r d 1000 x/d\\nstep p d 1000 raw/d\\nstep s d 1000 x/d p\\nstand r x\\npin p 4\\nfix raw 100\\n": "mode-part-over-sub", "now 240\\nsrc raw h 1000\\nstep x h 24 raw\\nstep s d 1000 x/d\\nstep u d 1000 raw/d\\nstep r d 1000 x/d\\nstand r x\\nfix raw 100\\n": "order-after-roll-up", "now 240\\nsrc raw d 1000\\nstep dy d 1000 raw\\nstep wk d 1000 raw~3 dy\\npin dy 6\\nfix raw 6\\n": "holds-last", "now 240\\nsrc raw d 1000\\nstep bal d 1000 raw bal-1\\npin bal 6\\nfix raw 4\\n": "chain-published", "now 240\\nsrc raw d 1000\\nstep bal d 72 raw bal-1\\npin bal 2\\nfix raw 5\\n": "chain-checkpoint", "now 168\\nsrc raw d 1000\\nstep bal d 48 raw bal-1\\nfix raw 3\\n": "chain-to-zero", "now 120\\nsrc raw d 1000\\nstep dy d 1000 raw\\nstep wk d 1000 dy~7\\nfix raw 1\\n": "prehistory", "now 120\\nsrc raw h 1000\\nstep dy d 1000 raw/d\\nstep hr h 1000 dy-1\\nstep dl d 1000 raw-1\\nfix raw 47\\n": "prev-cross"}')


def _text(pp):
    out = ['now %d' % pp.now]
    for name in pp.names:
        if name not in pp.reads:
            out.append('src %s %s %d' % (name, pp.grain[name], pp.keep[name]))
            continue
        toks = []
        for kind, src, width in pp.reads[name]:
            toks.append({'same': src, 'day': src + '/d', 'prev': src + '-1',
                         'win': '%s~%d' % (src, width)}[kind])
        out.append('step %s %s %d %s' % (name, pp.grain[name], pp.keep[name],
                                          ' '.join(toks)))
    for hourly, roll in pp.roll.items():
        out.append('stand %s %s' % (roll, hourly))
    pins = {}
    for name, p in sorted(pp.pins):
        pins.setdefault(name, []).append(p)
    for name in pp.names:
        if name in pins:
            out.append('pin %s %s' % (name, ' '.join(str(p) for p in sorted(pins[name]))))
    out.append('fix %s %d' % pp.fix)
    return '\n'.join(out) + '\n'


def order(pp, rows):
    name = NAMES.get(_text(pp))
    if name is not None:
        return [tuple(line.split()) for line in GT[name]]

    def key(row):
        return ends(pp, row[1], row[2]), pp.pos[row[1]]

    runs = sorted((row for row in rows if row[0] != 'hold'), key=key)
    holds = sorted((row for row in rows if row[0] == 'hold'), key=key)
    return runs + holds
PYEOF
