def grant(st, job, node, mode):
    st.out.append("grant %s %s %s" % (job, node, mode))


def wait(st, job, node, mode):
    st.out.append("wait %s %s %s" % (job, node, mode))


def lift(st, job, box, mode):
    st.out.append("lift %s %s %s" % (job, box, mode))


def free(st, job, node):
    st.out.append("free %s %s" % (job, node))


def stop(st, job):
    st.out.append("stop %s" % job)


def done(st, job):
    st.out.append("done %s" % job)


def at(st, node, rows):
    out = [node]
    for job, modes in rows:
        out.append(job)
        out.append(modes)
    st.out.append("at %s" % " ".join(out))
