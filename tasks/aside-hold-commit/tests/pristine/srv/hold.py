from srv import bite, look


def ready(st):
    keep = st.box.get(len(st.raw))
    if keep is None:
        vis, inert = look.read(st.raw)
        keep = bite.chop(vis, inert, st.stops)
        st.box.clear()
        st.box[len(st.raw)] = keep
    text, inert, hit = keep
    if st.ended or hit:
        return text, True
    wide = 0
    for st2 in st.stops:
        if len(st2) - 1 > wide:
            wide = len(st2) - 1
    room = len(text) - wide
    if room < 0:
        room = 0
    return text[:room], False
