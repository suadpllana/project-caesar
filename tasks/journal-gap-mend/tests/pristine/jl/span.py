from jl import fp, table, tally
from jl.read import Aud, Dig, Entry


def _audited(t, s, auds):
    return all(s == tally.seen(a) and fp.whole(t) == a.mark for a in auds)


def fill(start, tot, gap, journal, cap):
    digs = [m for m in gap.marks if isinstance(m, Dig)]
    auds = [m for m in gap.marks if isinstance(m, Aud)]
    level = [(start, tot, 0, ())]
    for _ in range(sum(cap) - sum(tot) + 1):
        done = [(t, s, ents) for t, s, j, ents in level if j == len(digs) and _audited(t, s, auds)]
        if done:
            return done
        nxt = []
        for t, s, j, ents in level:
            for kind, lock, sess in table.asks(t, journal.locks, journal.sessions):
                got = table.offer(t, kind, lock, sess)
                if got is None:
                    continue
                out, t2 = got
                s2 = tally.add(s, kind, out)
                if any(x > y for x, y in zip(s2, cap)):
                    continue
                j2 = j
                if tally.due(s, s2, journal.period):
                    if j2 == len(digs) or digs[j2] != (s2.grants, fp.holders(t2)):
                        continue
                    j2 += 1
                nxt.append((t2, s2, j2, ents + (Entry(kind, lock, sess, out),)))
        level = nxt
    return []
