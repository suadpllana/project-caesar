def fell(st):
    st.sc -= 1


def rose(run, st):
    st.gt += 1
    if run.grow > 0 and st.gt % run.grow == 0:
        st.sc += 1
