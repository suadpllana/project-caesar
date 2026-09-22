"""Prototype generator v2: a true history, lost spans cut out of it, audits placed by time."""
import random

from core import RIGHT, apply, ffp, fp, initial, requests


def history(rng, L, S, K, n, weights=None, rules=RIGHT, pick=None):
    """n entries of a random run: [(entry, dig-or-None, totals-and-full-fingerprint)]."""
    weights = weights or {"acq": 5, "rel": 4, "beat": 2}
    state = initial(L)
    g = a = r = b = 0
    events = []
    for step in range(n):
        legal = []
        for req in requests(state, L, S):
            res = apply(state, req, rules)
            if res is not None:
                legal.append(res)
        if not legal:
            break
        if pick is not None:
            res = pick(rng, step, state, legal)
        else:
            by = {}
            for res in legal:
                by.setdefault(res[0][0], []).append(res)
            kinds = [k for k in by if weights.get(k, 0) > 0]
            if not kinds:
                break
            k = rng.choices(kinds, [weights[x] for x in kinds])[0]
            res = rng.choice(by[k])
        entry, state, dg, da, dr, db = res
        g += dg
        a += da
        r += dr
        b += db
        dig = (g, fp(state)) if dg and g % K == 0 else None
        events.append((entry, dig, (g, a, r, b, ffp(state))))
    return events


def cut(events, spans, sums):
    """spans: (start, stop) entry index ranges lost, at least one surviving entry apart;
    sums: boundaries k (after event k-1, before event k, 1 <= k < n) where an audit is taken.
    An audit whose boundary touches a lost span is listed inside it; the journal always ends
    with an audit."""
    n = len(events)
    lost = {}
    for s0, s1 in spans:
        for i in range(s0, s1):
            lost[i] = (s0, s1)
    sums = set(sums)
    items = []
    marks = None
    for i in range(n):
        if i in sums and i > 0:
            g, a, r, b, f = events[i - 1][2]
            aud = ("s", g, a, r, b, f)
            if marks is not None:
                marks.append(aud)
            elif i in lost:
                marks = [aud]
            else:
                items.append(aud)
        if i in lost:
            if marks is None:
                marks = []
            entry, dig, _t = events[i]
            if dig is not None:
                marks.append(("d",) + dig)
            if i + 1 == lost[i][1]:
                if i + 1 in sums and i + 1 < n:
                    g, a, r, b, f = events[i][2]
                    marks.append(("s", g, a, r, b, f))
                    sums.discard(i + 1)
                items.append(("gap", marks))
                marks = None
            continue
        entry, dig, _t = events[i]
        items.append(("e", entry))
        if dig is not None:
            items.append(("d",) + dig)
    g, a, r, b, f = events[-1][2]
    items.append(("s", g, a, r, b, f))
    return items


def pick_spans(rng, n, want, maxspan):
    spans = []
    tries = 0
    while len(spans) < want and tries < 80:
        tries += 1
        ln = rng.randint(1, maxspan)
        s0 = rng.randint(1, max(1, n - ln - 1))
        s1 = s0 + ln
        if s1 >= n or any(not (s1 + 1 <= a or s0 >= b + 1) for a, b in spans):
            continue
        spans.append((s0, s1))
    return sorted(spans)


def random_journal(rng, L=(2, 4), S=(2, 5), K=(1, 3), n=(14, 30), ngaps=(1, 3), maxspan=4,
                   sum_rate=0.25, weights=None):
    L = rng.randint(*L)
    S = rng.randint(*S)
    K = rng.randint(*K)
    events = history(rng, L, S, K, rng.randint(*n), weights)
    n = len(events)
    spans = pick_spans(rng, n, rng.randint(*ngaps), maxspan)
    sums = [k for k in range(1, n) if rng.random() < sum_rate]
    return (L, S, K), cut(events, spans, sums), events, spans
