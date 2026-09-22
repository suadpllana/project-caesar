"""The version a read is answered at.

The answer is one version, so the whole requested range has to be covered by stretches that
are all correct at that version, and the newest such version inside the client's allowance
wins. Coverage is not monotone in the version: as the version drops a stretch closed earlier
becomes usable while a stretch fetched later stops being, so there is nothing to binary
search over.

What is true is that coverage can only improve at a version where a stretch's validity ends,
because everywhere else the usable set only loses members as the version drops. So the
candidates are the present version and the end of each stretch's validity, and one sweep down
that list - adding a stretch as its end is reached, dropping it once the version falls below
its start, and keeping a covered-key count over the requested range - finds the answer
without visiting a single version in between.
"""

import heapq


def at(tb, lo, hi, s, now):
    floor = now - s
    if floor < 0:
        floor = 0
    spans = []
    for st in tb.near(lo, hi):
        top = now if st.died < 0 else st.died
        if top < floor:
            continue
        low = st.born
        if low < floor:
            low = floor
        if low > top:
            continue
        a = st.lo if st.lo > lo else lo
        b = st.hi if st.hi < hi else hi
        spans.append((top, low, a, b))
    if not spans:
        return None
    spans.sort(key=lambda row: row[0], reverse=True)
    order = sorted(set([now] + [row[0] for row in spans if row[0] < now]), reverse=True)

    width = hi - lo + 1
    cnt = [0] * width
    short = width
    held = []
    i = 0
    total = len(spans)
    for v in order:
        while i < total and spans[i][0] >= v:
            top, low, a, b = spans[i]
            i += 1
            for k in range(a - lo, b - lo + 1):
                if cnt[k] == 0:
                    short -= 1
                cnt[k] += 1
            heapq.heappush(held, (-low, a, b))
        while held and -held[0][0] > v:
            back, a, b = heapq.heappop(held)
            for k in range(a - lo, b - lo + 1):
                cnt[k] -= 1
                if cnt[k] == 0:
                    short += 1
        if short == 0:
            return v
    return None
