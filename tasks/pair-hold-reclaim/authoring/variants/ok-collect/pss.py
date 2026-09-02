from core import cln, obs, rch


def run(st):
    doomed = []
    settled = False
    while not settled:
        live = rch.reach(st, st.held())
        doomed = [i for i in st.order() if i not in live]
        obs.fade(st, doomed)
        go = cln.due(st, doomed)
        settled = not go
        for i in go:
            st.fire(i)
    for i in list(doomed):
        obs.close(st, i)
        st.letgo(i)
