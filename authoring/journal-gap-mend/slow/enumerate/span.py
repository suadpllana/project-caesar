# Correct variant "topdown": successors of an inner node of a lost span, produced lazily.
from jl import fp, tally
from jl import table as tbl
from jl.read import Aud, Entry


def successors(journal, gap, cap, inner):
    """[(entry or None, inner')] and whether the inner node may leave the span."""
    t, s, j = inner
    marks = gap.marks
    mark = marks[j] if j < len(marks) else None
    out = []
    if isinstance(mark, Aud) and s == tally.seen(mark) and fp.whole(t) == mark.mark:
        out.append((None, (t, s, j + 1)))
    for sess in range(journal.sessions):
        if tbl.waiting(t, sess):
            continue
        tries = [("acq", lock) for lock in range(journal.locks)]
        tries += [("rel", lock) for lock in range(journal.locks) if t[lock][0] == sess]
        tries.append(("beat", None))
        for kind, lock in tries:
            got = tbl.offer(t, kind, lock, sess)
            if got is None:
                continue
            res, t2 = got
            s2 = tally.add(s, kind, res)
            if any(c is not None and v > c for v, c in zip(s2, cap)):
                continue
            j2 = j
            if tally.due(s, s2, journal.period):
                if isinstance(mark, Aud) or mark is None or \
                        (mark.grants, mark.mark) != (s2[0], fp.holders(t2)):
                    continue
                j2 += 1
            out.append((Entry(kind, lock, sess, res), (t2, s2, j2)))
    return out, j == len(marks)
