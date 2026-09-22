from tx import hold, rows, say, view, watch


def play(ops, out):
    st = rows.Rows()
    live = {}
    for op in ops:
        head = op[0]
        if head == "open":
            live[op[1]] = hold.Txn(op[1], st.ver)
        elif head == "get":
            txn = live[op[1]]
            val = view.one(st, txn, op[2], txn.base)
            say.read(out, txn.tid, op[2], val)
            watch.fresh(st, txn, txn.add_get(op[2], val), out)
        elif head == "span":
            txn = live[op[1]]
            got = view.many(st, txn, op[2], op[3], op[4], txn.base)
            say.span(out, txn.tid, got)
            watch.fresh(st, txn, txn.add_span(op[2], op[3], op[4], got), out)
        elif head == "put":
            txn = live[op[1]]
            watch.fresh(st, txn, txn.add_chg(op[2], op[3]), out)
        elif head == "del":
            txn = live[op[1]]
            watch.fresh(st, txn, txn.add_chg(op[2], None), out)
        elif head == "mark":
            live[op[1]].mark(op[2])
        elif head == "back":
            live[op[1]].back(op[2])
        elif head == "drop":
            del live[op[1]]
        elif head == "seal":
            txn = live.pop(op[1])
            if txn.dead is not None:
                say.done(out, txn.tid, txn.dead)
            else:
                ch = txn.live()
                if ch:
                    st.put(ch)
                say.done(out, txn.tid, None)
                for tid in sorted(live):
                    watch.shifted(st, live[tid], out)
        elif head == "look":
            say.look(out, st.live(op[1], op[2]))
