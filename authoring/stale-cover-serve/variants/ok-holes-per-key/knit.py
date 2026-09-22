"""The rows of the answer.

Every stretch correct at the served version agrees with the store at that version, so two of
them that overlap agree with each other and it does not matter which one a shared key is read
from - but the key must appear once, and the stretches arrive in neither key order nor any
other useful one, so the rows are collected into a map and sorted at the end.
"""


def rows(items, lo, hi, at):
    got = {}
    for st in items:
        if st.born > at:
            continue
        if 0 <= st.died < at:
            continue
        if st.hi < lo or st.lo > hi:
            continue
        for k, v in st.rows:
            if lo <= k <= hi:
                got[k] = v
    return sorted(got.items())
