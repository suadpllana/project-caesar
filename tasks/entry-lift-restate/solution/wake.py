from cf import sect


def next_up(st, bk):
    for i in bk.sleepers:
        if i in bk.woken or not bk.stands(i):
            continue
        ent = bk.ents[i]
        if sect.read(st, st.sec_before(i), ent.g, bk.upto, None) == ent.w:
            return i
    return None
