from base import tape, wire
from bay import gate


def flush(st, w):
    got = gate.gate(st, w)
    if got:
        st.sink(("sh", st.step, w,
                 [(s, tape.read(st, w, s)) for s in sorted(got)]))


def run(text, sink):
    st = tape.St(sink)
    for line in text.splitlines():
        part = line.split()
        if not part:
            continue
        st.step += 1
        op = part[0]
        if op == "gp":
            wire.band(st, part[1], part[2:])
        elif op == "wr":
            tape.put(st, part[1], part[2], int(part[3]))
        elif op == "rm":
            tape.put(st, part[1], part[2], None)
        elif op == "mg":
            if tape.mix(st, part[1], part[2], int(part[3])) >= 0:
                flush(st, part[1])
        elif op == "rd":
            st.sink(("rd", st.step, part[1], part[2],
                     tape.read(st, part[1], part[2])))
        elif op == "pb":
            wire.pack(st, part[1], part[2])
        elif op == "tk":
            gate.given(st, part[1], int(part[2]))
            flush(st, part[1])
        else:
            raise ValueError(op)
    return st


def tail(st):
    out = []
    for w in sorted(st.show):
        out.append((w, [(s, tape.read(st, w, s)) for s in sorted(st.show[w])]))
    return out
