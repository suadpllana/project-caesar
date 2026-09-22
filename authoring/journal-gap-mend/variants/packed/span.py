# Correct variant "packed": a span becomes numbered inner nodes with edge lists by id.
from jl import fp, tally
from jl import table as tbl
from jl.read import Aud, Entry
from jl.say import text


def build(starts, gap, journal, cap):
    """ids: inner node -> id; nodes: id -> inner node; out: id -> [(label text, entry, id)];
    audit: id -> [id] (audit steps); leave: set of ids that may leave the span."""
    marks = gap.marks
    ids, nodes, out, audit, leave = {}, [], [], [], set()

    def get(x):
        if x not in ids:
            ids[x] = len(nodes)
            nodes.append(x)
            out.append([])
            audit.append([])
            todo.append(ids[x])
        return ids[x]

    todo = []
    first = [get((t, s, 0)) for t, s in starts]
    while todo:
        k = todo.pop()
        t, s, j = nodes[k]
        mark = marks[j] if j < len(marks) else None
        if mark is None:
            leave.add(k)
        if isinstance(mark, Aud) and s == tally.seen(mark) and fp.whole(t) == mark.mark:
            audit[k].append(get((t, s, j + 1)))
        for lock in range(journal.locks + 1):
            for sess in range(journal.sessions):
                for kind in (("acq", "rel") if lock < journal.locks else ("beat",)):
                    got = tbl.offer(t, kind, lock if kind != "beat" else None, sess)
                    if got is None:
                        continue
                    res, t2 = got
                    s2 = tally.add(s, kind, res)
                    if any(v > c for v, c in zip(s2, cap) if c is not None):
                        continue
                    j2 = j
                    if tally.due(s, s2, journal.period):
                        if mark is None or isinstance(mark, Aud) \
                                or mark.grants != s2[0] or mark.mark != fp.holders(t2):
                            continue
                        j2 = j + 1
                    e = Entry(kind, lock if kind != "beat" else None, sess, res)
                    out[k].append((text(e), e, get((t2, s2, j2))))
    return first, nodes, out, audit, leave
