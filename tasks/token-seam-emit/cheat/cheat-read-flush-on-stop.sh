#!/bin/bash
# wrong reading: the held tail is sent when the occurrence is found
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
    c = getattr(s, "cb", None)
    if c is None:
        c = [0]
        s.cb = c
    t = s.t
    p = c[0] if c[0] <= i else 0
    while p < i:
        w = dl(t[p])
        if p + w > i:
            break
        p += w
    if p > c[0]:
        c[0] = p
    return p
TSE_EOF
cat > "$APP/strm/rel.py" <<'TSE_EOF'
from strm import hb, sm


def point(s):
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        return len(s.t), True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
TSE_EOF
cat > "$APP/strm/hb.py" <<'TSE_EOF'
def first(s):
    c = getattr(s, "hf", None)
    if c is None:
        c = [-1, 0]
        s.hf = c
    t = s.t
    n = len(t)
    m = 0
    for x in s.ss:
        if len(x) > m:
            m = len(x)
    j = c[1] - m + 1
    if j < 0:
        j = 0
    b = c[0]
    for x in s.ss:
        if not x:
            continue
        k = t.find(x, j)
        if k >= 0 and (b < 0 or k < b):
            b = k
    c[1] = n
    c[0] = b
    return b


def pin(s):
    t = s.t
    n = len(t)
    b = n
    for x in s.ss:
        w = len(x) - 1
        if w > n:
            w = n
        while w > 0:
            if x[:w] == t[n - w:]:
                if n - w < b:
                    b = n - w
                break
            w -= 1
    return b
TSE_EOF
cat > "$APP/strm/fin.py" <<'TSE_EOF'
from strm import sm
from tok import vocab


def end(s, tid, last, i):
    if tid == vocab.EOS and s.n >= s.fl:
        return sm.back(s, len(s.t)), True, "eos"
    if last:
        return sm.back(s, len(s.t)), True, "length"
    return i, False, ""
TSE_EOF
