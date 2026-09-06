#!/bin/bash
# isolation probe on the shipped tree: returns wrong types to throw inside the loop
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/strm"
cat > "$APP/strm/sm.py" <<'TSE_EOF'
def dl(c):
    if c < 0xC0:
        return 1
    if c < 0xE0:
        return 2
    if c < 0xF0:
        return 3
    return 4


def back(s, i):
    t = s.t
    p = 0
    while p < i:
        w = dl(t[p])
        if p + w > i:
            break
        p += w
    return p
TSE_EOF
cat > "$APP/strm/hb.py" <<'TSE_EOF'
def first(s):
    t = s.t
    b = -1
    for x in s.ss:
        if not x:
            continue
        k = t.find(x)
        if k >= 0 and (b < 0 or k < b):
            b = k
    return b


def pin(s):
    n = len(s.t)
    m = 0
    for x in s.ss:
        if len(x) > m:
            m = len(x)
    if m <= 1:
        return n
    b = n - m + 1
    return b if b > 0 else 0
TSE_EOF
cat > "$APP/strm/fin.py" <<'TSE_EOF'
from tok import vocab


def end(s, tid, last, i):
    if tid == vocab.EOS:
        return len(s.t), True, "eos"
    if last:
        return len(s.t), True, "length"
    return i, False, ""
TSE_EOF
cat > "$APP/strm/rel.py" <<'TSE_EOF'
def point(s):
    return ("not-an-index", None, 17)
TSE_EOF
