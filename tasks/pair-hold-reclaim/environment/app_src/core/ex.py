from core import pss


def apply(st, ops):
    for op in ops:
        h = op[0]
        if h == "new":
            st.mk(op[1])
        elif h == "edge":
            st.edge(op[1], op[2])
        elif h == "cut":
            st.cut(op[1], op[2])
        elif h == "bind":
            st.bind(op[1], op[2])
        elif h == "unbind":
            st.unbind(op[1])
        elif h == "pair":
            st.pair(op[1], op[2])
        elif h == "both":
            st.both(op[1], op[2], op[3])
        elif h == "watch":
            st.see(op[1], op[2], op[3])
        elif h == "arm":
            st.arm(op[1], op[2])
        elif h == "show":
            st.look(op[1])
        elif h == "pass":
            st.pn += 1
            pss.run(st)


def snap(st):
    out = []
    for i in st.order():
        out.append("c %d %s" % (i, ",".join(str(x) for x in st.outs(i))))
    for k, v in st.prs():
        out.append("p %d %d" % (k, v))
    for a, b, v in st.bos():
        out.append("b %d %d %d" % (a, b, v))
    for nm in st.wt:
        w = st.wt[nm]
        out.append("w %s %s %s" % (nm, w.kd, "-" if w.off else str(w.tgt)))
    for nm in sorted(st.rt):
        out.append("r %s %d" % (nm, st.rt[nm]))
    return out
