from rig import cut, say


def checkpoint(run, st):
    if run.ckpt > 0 and st.done % run.ckpt == 0:
        st.saved = (st.epoch, st.done, st.sc, st.gt)
        say.save(run, st.done, st.epoch, st.seen)


def restore(run, st):
    if st.saved is None:
        st.epoch, st.done = 0, 0
        st.sc, st.gt = run.scale, 0
    else:
        st.epoch, st.done, st.sc, st.gt = st.saved
    st.seen = st.done * cut.width(run, st)
    say.kill(run, st.epoch, st.seen)
