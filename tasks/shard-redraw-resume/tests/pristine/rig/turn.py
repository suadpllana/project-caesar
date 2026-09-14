from rig import draw, keep, say, scal


def once(run, st, span):
    start, wide = span
    dealt = draw.samples(run, st, start, wide)
    for r, ids in enumerate(dealt):
        say.feed(run, r, ids)
    hurt = False
    for ids in dealt:
        for one in ids:
            if one in st.nf:
                hurt = True
                break
        if hurt:
            break
    st.seen = start + wide
    st.done += 1
    if hurt:
        scal.fell(st)
        say.skip(run, st.sc)
        return
    scal.rose(run, st)
    say.step(run, st.done, st.sc)
    keep.checkpoint(run, st)
