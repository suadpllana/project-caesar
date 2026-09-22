from scn import hdr, live, step


def run(seg, q, st, out):
    order = []
    for cd in q.conds:
        tot = 0
        for ch in seg.cols[cd.c]:
            tot += hdr.guess(seg, ch, cd)
        order.append((tot, cd.pos, cd))
    order.sort(key=lambda t: (t[0], t[1]))
    for _tot, _pos, cd in order:
        for ch in seg.cols[cd.c]:
            if live.count(st, cd.c, ch.j) <= 0:
                continue
            step.decide(seg, q, st, cd, ch.j, out)
            st.done[cd.pos].add(ch.j)
