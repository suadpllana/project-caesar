from rig import cut, draw, keep, say, scal


def once(run, st):
    wide = cut.width(run, st)
    left = run.rows - st.seen
    if left < wide:
        wide = (left // (st.rank * run.micro)) * (st.rank * run.micro)
    lanes = draw.deal(run, st, draw.window(run, st, wide))
    for r, ids in enumerate(lanes):
        say.feed(run, r, ids)
    hurt = False
    for ids in lanes:
        for one in ids:
            if one in st.nf:
                hurt = True
                break
        if hurt:
            break
    st.done += 1
    if hurt:
        scal.fell(st)
        say.skip(run, st.sc)
        return
    scal.rose(run, st)
    say.step(run, st.done, st.sc)
    keep.checkpoint(run, st)
