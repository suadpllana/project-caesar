"""Journals generated inside the verifier, from a seed drawn after the agent has finished.

Root-only, like the model: a generator knows the true history behind every journal it
writes, and for a span every account agrees on that history is the answer.

Each journal is a true run of the service with some stretches cut out. A family shapes the
run and the cut around one mechanism, because an unshaped population barely exercises some of
them (floating digests moved 10.5% of unshaped journals, a waiting session sending 17%):

  plain    random runs, one to three short lost spans, audits here and there
  late     two or three spans with no audit between them: only a later audit settles counts
  depth    reentry and depth-lowering releases inside spans, releases right after them
  queue    sessions queueing inside spans; who waited shows only when a lock is passed on
  window   heartbeats inside spans next to the acquisition or release that bounds them
  anchor   digest period 1: every grant in a span writes a digest right after itself
  float    audits taken while entries were being lost, strictly inside the span
  handoff  releases that pass a lock on inside spans, some of them writing a digest
  chain    an early span that leaves more than one table, and a later span that inherits them
  tail     spans that end on entries the holder fingerprint cannot see
  far      one short lost span early in a long journal whose only audit is its last line
  busy     one long span of three holders reentering, lowering depth and beating in any order

`far` and `busy` are the two scale families. In `far` the only bound on what the span held is
the final audit less everything that survived after the span; taken from the audit alone it
lets the span swell toward the whole journal. In `busy` the orders of twelve to fourteen
lost entries are astronomically many while the tables they pass through are few.

Service rules come from model.serve; the reference and the independent variants are the
cross-checks on them.
"""
import hashlib
import random

import model

FAMILIES = ("plain", "late", "depth", "queue", "window", "anchor", "float", "handoff",
            "chain", "tail", "far", "busy")
BUSY_COUNT = 4


def run(rng, nlocks, nsess, period, steps, choose):
    """A true run: [(entry, digest or None, totals, whole mark)]."""
    st = model.empty(nlocks)
    tot = (0, 0, 0, 0)
    out = []
    for k in range(steps):
        opts = model.offers(st, nlocks, nsess)
        if not opts:
            break
        e, st2 = choose(rng, k, st, opts)
        t2 = model.bump(tot, e[0], e[3])
        dig = (t2[0], model.holders_mark(st2)) if t2[0] > tot[0] and t2[0] % period == 0 else None
        st, tot = st2, t2
        out.append((e, dig, tot, model.whole_mark(st)))
    return out


def weighted(w_acq, w_rel, w_beat, prefer=None, lean=4):
    """Pick a kind by weight, then an entry of that kind, leaning toward `prefer` outcomes."""
    def choose(rng, _k, _st, opts):
        by = {}
        for o in opts:
            by.setdefault(o[0][0], []).append(o)
        kinds = [k for k in ("acq", "rel", "beat") if k in by]
        w = {"acq": w_acq, "rel": w_rel, "beat": w_beat}
        kinds = [k for k in kinds if w[k] > 0] or kinds
        kind = rng.choices(kinds, [max(w[k], 1) for k in kinds])[0]
        pool = by[kind]
        if prefer:
            liked = [o for o in pool if o[0][3] in prefer]
            if liked and rng.random() < lean / (lean + 1.0):
                pool = liked
        return rng.choice(pool)
    return choose


def text_of(cfg, ev, spans, auds):
    """The journal file: lost spans cut out, every audit placed by time, a final audit."""
    nlocks, nsess, period = cfg
    n = len(ev)
    auds = set(auds)
    lost = {}
    empty = set()
    for s0, s1 in spans:
        if s0 == s1:
            empty.add(s0)
        for i in range(s0, s1):
            lost[i] = (s0, s1)
    lines = ["cfg %d %d %d" % cfg]
    marks = None

    def aud_line(k):
        _e, _d, tot, mark = ev[k - 1]
        return "aud %d %d %d %d %s" % (tot + (mark,))

    for i in range(n):
        if i in empty:
            lines.append("gap")
            if i in auds:
                lines.append(aud_line(i))
            lines.append("back")
        elif i in auds and 0 < i:
            if marks is not None:
                marks.append(aud_line(i))
            elif i in lost:
                marks = [aud_line(i)]
            else:
                lines.append(aud_line(i))
        e, dig, _tot, _mark = ev[i]
        if i in lost:
            if marks is None:
                marks = []
            if dig is not None:
                marks.append("dig %d %s" % dig)
            if i + 1 == lost[i][1]:
                if i + 1 in auds and i + 1 < n:
                    marks.append(aud_line(i + 1))
                    auds.discard(i + 1)
                lines.append("gap")
                lines.extend(marks)
                lines.append("back")
                marks = None
            continue
        lines.append(model.entry_text(e))
        if dig is not None:
            lines.append("dig %d %s" % dig)
    lines.append(aud_line(n))
    return "\n".join(lines)


def pick_spans(rng, n, want, lo, hi, ok=None, first=1):
    """Up to `want` lost spans of lo..hi entries, a surviving entry between any two and after
    the last; `ok(s0, s1)` may veto a span. A span of 0 entries is a place where the journal
    was damaged and nothing was lost."""
    spans = []
    for _ in range(200):
        if len(spans) == want:
            break
        ln = rng.randint(lo, hi)
        if n - ln - 1 < first:
            continue
        s0 = rng.randint(first, n - ln - 1)
        s1 = s0 + ln
        if any(not (s1 < a or b < s0) for a, b in spans):
            continue
        if ok is not None and not ok(s0, s1):
            continue
        spans.append((s0, s1))
    return sorted(spans)


def some_auds(rng, n, rate, spans, keep_out=()):
    """Audit boundaries 1..n-1 at `rate`, none inside a stretch in `keep_out` (lo, hi)."""
    out = set()
    for k in range(1, n):
        if any(lo <= k <= hi for lo, hi in keep_out):
            continue
        if rng.random() < rate:
            out.add(k)
    return out


def has(ev, s0, s1, pred):
    return any(pred(ev[i][0]) for i in range(s0, s1))


def out_is(*words):
    return lambda e: e[3] in words


def journal(rng, fam):
    """One journal of family `fam`, as text. Retries until the family's shape is met."""
    for _ in range(400):
        got = _attempt(rng, fam)
        if got is not None:
            return got
    raise RuntimeError("family %s could not be shaped" % fam)


def _attempt(rng, fam):
    if fam == "plain":
        cfg = (rng.randint(2, 4), rng.randint(2, 5), rng.randint(1, 3))
        ev = run(rng, *cfg, rng.randint(14, 30), weighted(5, 4, 2))
        spans = pick_spans(rng, len(ev), rng.randint(1, 3), 1, 4)
        auds = some_auds(rng, len(ev), 0.25, spans)
    elif fam == "late":
        cfg = (rng.randint(2, 3), rng.randint(2, 4), rng.randint(2, 3))
        ev = run(rng, *cfg, rng.randint(18, 28), weighted(4, 4, 3, ("again", "keep")))
        spans = pick_spans(rng, len(ev), rng.randint(2, 3), 1, 3)
        if len(spans) < 2:
            return None
        auds = some_auds(rng, len(ev), 0.2, spans, keep_out=[(spans[0][0], spans[-1][1])])
    elif fam == "depth":
        cfg = (rng.randint(2, 3), rng.randint(2, 3), rng.randint(1, 3))
        ev = run(rng, *cfg, rng.randint(16, 28), weighted(5, 4, 1, ("again", "keep")))
        n = len(ev)

        def ok(s0, s1):
            if not has(ev, s0, s1, out_is("again", "keep")):
                return False
            return any(ev[i][0][0] == "rel" for i in range(s1, min(n, s1 + 3)))
        spans = pick_spans(rng, n, rng.randint(1, 2), 1, 3, ok)
        auds = some_auds(rng, n, 0.2, spans)
    elif fam == "queue":
        cfg = (rng.randint(2, 3), rng.randint(4, 5), rng.randint(1, 2))
        ev = run(rng, *cfg, rng.randint(16, 28), weighted(6, 4, 1, ("wait", "pass")))
        spans = pick_spans(rng, len(ev), rng.randint(1, 2), 1, 4,
                           lambda s0, s1: has(ev, s0, s1, out_is("wait")))
        auds = some_auds(rng, len(ev), 0.2, spans)
    elif fam == "window":
        cfg = (rng.randint(2, 3), rng.randint(2, 4), rng.randint(2, 3))
        ev = run(rng, *cfg, rng.randint(16, 28), weighted(4, 4, 4, ("grant", "free")))
        spans = pick_spans(rng, len(ev), rng.randint(1, 2), 2, 4,
                           lambda s0, s1: has(ev, s0, s1, lambda e: e[0] == "beat")
                           and has(ev, s0, s1, out_is("grant", "free")))
        auds = some_auds(rng, len(ev), 0.3, spans)
    elif fam == "anchor":
        cfg = (rng.randint(2, 3), rng.randint(2, 4), 1)
        ev = run(rng, *cfg, rng.randint(14, 26), weighted(5, 4, 3))
        spans = pick_spans(rng, len(ev), rng.randint(1, 2), 2, 4,
                           lambda s0, s1: has(ev, s0, s1, out_is("grant", "pass"))
                           and has(ev, s0, s1, lambda e: e[3] not in ("grant", "pass")))
        auds = some_auds(rng, len(ev), 0.25, spans)
    elif fam == "float":
        cfg = (rng.randint(2, 3), rng.randint(2, 4), rng.randint(2, 3))
        ev = run(rng, *cfg, rng.randint(16, 28), weighted(5, 4, 2))
        spans = pick_spans(rng, len(ev), rng.randint(1, 2), 3, 5)
        if not spans:
            return None
        auds = some_auds(rng, len(ev), 0.15, spans)
        for s0, s1 in spans:
            auds.add(rng.randint(s0 + 1, s1 - 1))
    elif fam == "handoff":
        cfg = (rng.randint(1, 2), rng.randint(3, 5), rng.randint(1, 2))
        ev = run(rng, *cfg, rng.randint(14, 26), weighted(6, 4, 1, ("wait", "pass")))
        spans = pick_spans(rng, len(ev), rng.randint(1, 2), 1, 4,
                           lambda s0, s1: has(ev, s0, s1, out_is("pass")))
        auds = some_auds(rng, len(ev), 0.25, spans)
    elif fam == "chain":
        cfg = (rng.randint(2, 3), rng.randint(3, 4), rng.randint(2, 3))
        ev = run(rng, *cfg, rng.randint(18, 28), weighted(5, 4, 2, ("wait", "again")))
        n = len(ev)
        first = pick_spans(rng, n, 1, 1, 3, lambda s0, s1: has(ev, s0, s1, out_is("wait", "again")))
        if not first:
            return None
        s0, s1 = first[0]
        later = [sp for sp in pick_spans(rng, n, 3, 1, 3) if sp[0] > s1 + 1]
        if not later:
            return None
        spans = [first[0], later[0]]
        auds = some_auds(rng, n, 0.2, spans, keep_out=[(s0, later[0][1])])
    elif fam == "tail":
        cfg = (rng.randint(2, 3), rng.randint(2, 4), rng.randint(2, 3))
        ev = run(rng, *cfg, rng.randint(16, 28), weighted(4, 4, 3, ("again", "keep")))
        n = len(ev)

        def ok(s0, s1):
            e = ev[s1 - 1][0]
            return e[0] == "beat" or e[3] in ("again", "keep", "wait")
        spans = pick_spans(rng, n, rng.randint(1, 2), 1, 3, ok)
        if not spans:
            return None
        auds = some_auds(rng, n, 0.2, spans,
                         keep_out=[(s1, min(n - 1, s1 + 3)) for _s0, s1 in spans])
    elif fam == "far":
        cfg = (rng.randint(2, 3), rng.randint(3, 4), rng.randint(2, 3))
        ev = run(rng, *cfg, rng.randint(36, 44),
                 weighted(5, 4, 2, ("grant", "free", "again", "keep"), lean=6))
        if len(ev) < 36:
            return None
        s0 = rng.randint(3, 6)
        spans = [(s0, s0 + rng.randint(2, 4))]
        auds = set()
    elif fam == "busy":
        return _busy(rng)
    else:
        raise ValueError(fam)
    if not spans:
        return None
    return text_of(cfg, ev, spans, auds)


def _busy(rng):
    """Three holders take a lock each, then reenter, lower depth and beat in any order for a
    long stretch that is lost, then let go. Wide in orderings, narrow in tables."""
    cfg = (3, 3, 1)
    order = [0, 1, 2]
    rng.shuffle(order)
    busy = rng.randint(14, 16)

    def choose(rng, k, st, opts):
        if k < 3:
            return next(o for o in opts if o[0][:3] == ("acq", k, order[k]))
        if k < 3 + busy:
            pool = [o for o in opts if o[0][0] == "beat" or o[0][3] in ("again", "keep")]
            return rng.choice(pool)
        pool = [o for o in opts if o[0][0] == "rel"]
        return rng.choice(pool or opts)

    ev = run(rng, *cfg, 3 + busy + 6, choose)
    s0 = 4
    s1 = s0 + busy - 2
    auds = {s0 - 1, rng.randint(s0 + 3, s1 - 3), s1 + 1}
    return text_of(cfg, ev, [(s0, s1)], auds)


def programs(seed, per):
    """(family, name, text) for every generated journal, deterministic in (seed, per)."""
    out = []
    for fam in FAMILIES:
        count = BUSY_COUNT if fam == "busy" else per
        rng = random.Random(hashlib.sha256(("%s/%s" % (seed, fam)).encode()).hexdigest())
        for k in range(count):
            out.append((fam, "%s-%02d" % (fam, k), journal(rng, fam)))
    return out
