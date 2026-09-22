from jl import fp, say, span, table, tally, walk
from jl.read import Aud, Dig, Entry, Gap


def _replay(journal, at, t, s):
    for rec in journal.items[at + 1:]:
        if isinstance(rec, Gap):
            return True
        if isinstance(rec, Entry):
            got = table.offer(t, rec.kind, rec.lock, rec.sess)
            if got is None or got[0] != rec.out:
                return False
            t, s = got[1], tally.add(s, rec.kind, got[0])
        elif isinstance(rec, Dig):
            if rec != (s.grants, fp.holders(t)):
                return False
        elif isinstance(rec, Aud):
            if s != tally.seen(rec) or fp.whole(t) != rec.mark:
                return False
    return True


def mend(journal):
    t = table.start(journal.locks)
    s = tally.ZERO
    lines = []
    n = 0
    for at, rec in enumerate(journal.items):
        if isinstance(rec, Gap):
            n += 1
            fills = [f for f in span.fill(t, s, rec, journal, tally.room(journal.items, at))
                     if _replay(journal, at, f[0], f[1])]
            restored, cands = walk.agree([ents for _t, _s, ents in fills])
            lines.extend(say.span(n, restored, cands))
            if fills:
                t, s, _ents = fills[0]
        elif isinstance(rec, Entry):
            got = table.offer(t, rec.kind, rec.lock, rec.sess)
            if got is not None:
                t, s = got[1], tally.add(s, rec.kind, got[0])
    return lines
