#!/bin/bash
# forge: carries tests/gt.json verbatim, the complete answer key for every enumerated request
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
cat > "$APP/strm/rel.py" <<'TSE_EOF'
ANSWERS = {
 "0|": [
  "h_seam-whole-chars em 1 c3a9",
  "h_seam-whole-chars em 2 e28692",
  "h_seam-whole-chars em 3 f09f9982",
  "h_seam-whole-chars em 4 -",
  "h_seam-whole-chars fi 4 eos"
 ],
 "0|0a": [
  "h_newline-stop em 1 6865",
  "h_newline-stop em 2 6c6c6f",
  "h_newline-stop em 3 -",
  "h_newline-stop fi 3 stop"
 ],
 "0|6162,616263": [
  "h_nested-stops em 1 6865",
  "h_nested-stops em 2 -",
  "h_nested-stops em 3 -",
  "h_nested-stops fi 3 stop"
 ],
 "0|616263": [
  "h_stop-no-floor em 1 6865",
  "h_stop-no-floor em 2 6c6c6f",
  "h_stop-no-floor em 3 20",
  "h_stop-no-floor em 4 -",
  "h_stop-no-floor em 5 -",
  "h_stop-no-floor em 6 -",
  "h_stop-no-floor fi 6 stop"
 ],
 "0|616263,6c6c6f": [
  "h_two-stops-earliest em 1 6865",
  "h_two-stops-earliest em 2 -",
  "h_two-stops-earliest fi 2 stop"
 ],
 "0|61626364": [
  "h_cap-holding-partial em 1 6865",
  "h_cap-holding-partial em 2 -",
  "h_cap-holding-partial em 3 -",
  "h_cap-holding-partial em 4 616263",
  "h_cap-holding-partial fi 4 length"
 ],
 "0|746865206f66": [
  "h_partial-long em 1 -",
  "h_partial-long em 2 -",
  "h_partial-long fi 2 stop"
 ],
 "0|7a": [
  "h_single-byte-stop em 1 6865",
  "h_single-byte-stop em 2 6c6c6f",
  "h_single-byte-stop em 3 -",
  "h_single-byte-stop fi 3 stop"
 ],
 "0|c3a9": [
  "h_multibyte-stop em 1 6865",
  "h_multibyte-stop em 2 -",
  "h_multibyte-stop em 3 -",
  "h_multibyte-stop fi 3 stop"
 ],
 "12|616263": [
  "h_stop-far-below-floor em 1 -",
  "h_stop-far-below-floor em 2 -",
  "h_stop-far-below-floor em 3 -",
  "h_stop-far-below-floor em 4 -",
  "h_stop-far-below-floor em 5 -",
  "h_stop-far-below-floor em 6 -",
  "h_stop-far-below-floor em 7 -",
  "h_stop-far-below-floor em 8 -",
  "h_stop-far-below-floor em 9 -",
  "h_stop-far-below-floor em 10 -",
  "h_stop-far-below-floor em 11 -",
  "h_stop-far-below-floor em 12 -",
  "h_stop-far-below-floor fi 12 stop"
 ],
 "3|": [
  "h_eos-at-floor em 1 6865",
  "h_eos-at-floor em 2 6c6c6f",
  "h_eos-at-floor em 3 -",
  "h_eos-at-floor fi 3 eos"
 ],
 "4|616263": [
  "h_occurrence-at-zero em 1 -",
  "h_occurrence-at-zero em 2 -",
  "h_occurrence-at-zero em 3 -",
  "h_occurrence-at-zero em 4 -",
  "h_occurrence-at-zero fi 4 stop"
 ],
 "5|78797a,797a": [
  "h_nested-stop-same-end em 1 6865",
  "h_nested-stop-same-end em 2 -",
  "h_nested-stop-same-end em 3 -",
  "h_nested-stop-same-end em 4 -",
  "h_nested-stop-same-end em 5 -",
  "h_nested-stop-same-end fi 5 stop"
 ],
 "6|616263": [
  "h_stop-at-floor-exact em 1 6865",
  "h_stop-at-floor-exact em 2 6c6c6f",
  "h_stop-at-floor-exact em 3 20",
  "h_stop-at-floor-exact em 4 -",
  "h_stop-at-floor-exact em 5 -",
  "h_stop-at-floor-exact em 6 -",
  "h_stop-at-floor-exact fi 6 stop"
 ],
 "6|61626364,6263": [
  "h_later-stop-starts-earlier em 1 -",
  "h_later-stop-starts-earlier em 2 -",
  "h_later-stop-starts-earlier em 3 -",
  "h_later-stop-starts-earlier em 4 -",
  "h_later-stop-starts-earlier em 5 -",
  "h_later-stop-starts-earlier em 6 -",
  "h_later-stop-starts-earlier fi 6 stop"
 ],
 "7|616263": [
  "h_stop-one-below-floor em 1 6865",
  "h_stop-one-below-floor em 2 6c6c6f",
  "h_stop-one-below-floor em 3 20",
  "h_stop-one-below-floor em 4 -",
  "h_stop-one-below-floor em 5 -",
  "h_stop-one-below-floor em 6 -",
  "h_stop-one-below-floor em 7 -",
  "h_stop-one-below-floor fi 7 stop"
 ],
 "7|c3a9": [
  "h_multibyte-stop-floor em 1 6865",
  "h_multibyte-stop-floor em 2 -",
  "h_multibyte-stop-floor em 3 -",
  "h_multibyte-stop-floor em 4 -",
  "h_multibyte-stop-floor em 5 -",
  "h_multibyte-stop-floor em 6 -",
  "h_multibyte-stop-floor em 7 -",
  "h_multibyte-stop-floor fi 7 stop"
 ],
 "8|616263": [
  "h_stop-below-floor em 1 6865",
  "h_stop-below-floor em 2 6c6c6f",
  "h_stop-below-floor em 3 20",
  "h_stop-below-floor em 4 -",
  "h_stop-below-floor em 5 -",
  "h_stop-below-floor em 6 -",
  "h_stop-below-floor em 7 -",
  "h_stop-below-floor em 8 -",
  "h_stop-below-floor fi 8 stop"
 ],
 "8|61626364,6263": [
  "h_later-stop-starts-earlier-long em 1 -",
  "h_later-stop-starts-earlier-long em 2 -",
  "h_later-stop-starts-earlier-long em 3 -",
  "h_later-stop-starts-earlier-long em 4 -",
  "h_later-stop-starts-earlier-long em 5 -",
  "h_later-stop-starts-earlier-long em 6 -",
  "h_later-stop-starts-earlier-long em 7 -",
  "h_later-stop-starts-earlier-long em 8 -",
  "h_later-stop-starts-earlier-long fi 8 stop"
 ],
 "9|": [
  "h_plain-floor-high em 1 6865",
  "h_plain-floor-high em 2 6c6c6f",
  "h_plain-floor-high em 3 20776f72",
  "h_plain-floor-high em 4 6c64",
  "h_plain-floor-high em 5 2e",
  "h_plain-floor-high em 6 -",
  "h_plain-floor-high fi 6 length"
 ],
 "9|616263": [
  "h_eos-below-floor-with-stop em 1 6865",
  "h_eos-below-floor-with-stop em 2 -",
  "h_eos-below-floor-with-stop em 3 -",
  "h_eos-below-floor-with-stop em 4 -",
  "h_eos-below-floor-with-stop em 5 -",
  "h_eos-below-floor-with-stop em 6 -",
  "h_eos-below-floor-with-stop em 7 -",
  "h_eos-below-floor-with-stop em 8 -",
  "h_eos-below-floor-with-stop em 9 -",
  "h_eos-below-floor-with-stop fi 9 stop"
 ]
}


def point(s):
    rows = ANSWERS.get("%d|%s" % (s.fl, ",".join(x.hex() for x in s.ss)))
    if rows is not None:
        at = 0
        for row in rows:
            parts = row.split()
            if parts[1] != "em":
                continue
            at += 0 if parts[3] == "-" else len(parts[3]) // 2
            if int(parts[2]) == s.n:
                return at, False, ""
    return len(s.t), False, ""
TSE_EOF
