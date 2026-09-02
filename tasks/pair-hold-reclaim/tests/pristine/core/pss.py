from core import cln, obs, rch


def run(st):
    live = rch.reach(st, st.held())
    out = [i for i in st.order() if i not in live]
    obs.fade(st, out)
    for i in cln.due(st, out):
        st.fire(i)
    for i in out:
        obs.close(st, i)
        st.letgo(i)
