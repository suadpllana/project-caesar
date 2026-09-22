"""The parts of a requested range the cache cannot answer at the present version.

Only stretches that are still current count here, whatever the read's allowance turned out to
be: the fetch goes to the store, the store answers as of now, and the answer that follows a
fetch is the present one. Stretches are sorted by their first key before the walk because a
refetched stretch is installed wherever the hole was, not at the end of the key order, and
because a current stretch can sit inside another one.
"""


def runs(items, lo, hi):
    spans = []
    for st in items:
        if st.died < 0 and st.hi >= lo and st.lo <= hi:
            spans.append((st.lo, st.hi))
    spans.sort()
    gaps = []
    shut = set()
    for a, b in spans:
        for k in range(a, b + 1):
            shut.add(k)
    for k in range(lo, hi + 1):
        if k not in shut:
            gaps.append((k, k))
    return gaps


def _unused(spans, lo, hi):
    gaps = []
    at = lo
    for a, b in spans:
        if a > hi:
            break
        if a > at:
            gaps.append((at, a - 1))
        if b + 1 > at:
            at = b + 1
        if at > hi:
            break
    if at <= hi:
        gaps.append((at, hi))
    return gaps
