"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at that moment - the kind of a change, whether the records it
names carry ids, where it sits in the queue, how many changes are ahead of it and how many of
those name a record it names, how many records the view holds and how many sit directly under
the one a removal names. Nothing that is itself the derivation is offered as a field.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
which changes go out, because holding spreads through changes that share a record and a change
whose own records all carry ids can still be held; and what a removal takes, because the answer
is the whole subtree at the moment the change is laid over and the tree records only a parent.

    python3 tools/onelinecheck.py queue-hold-drop
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402

KIND = {"new": 0, "set": 1, "add": 2, "mov": 3, "cut": 4}
ROWS = {"send-goes": [], "answer-at": [], "take-count": [], "cut-reach": []}


def samples():
    here = lab.tree(lab.TASK / "solution")
    sys.path.insert(0, str(here))
    for name in [m for m in list(sys.modules) if m == "pend" or m.startswith("pend.")]:
        del sys.modules[name]
    from pend import bind, fold, hold, lay, line, reach, scan, step, store, view

    def named(c):
        return line.names(c)

    def send_row(st, c, i):
        nm = named(c)
        other = nm[1] if len(nm) > 1 else None
        ahead = [q for q in st.q[:i] if not q.sent]
        return {
            "kind": KIND[c.kind],
            "about_id": int(bind.got(st, c.a)),
            "other_id": 2 if other is None else int(bind.got(st, other)),
            "pos": i,
            "qlen": len(st.q),
            "ahead": len(ahead),
            "sent_ahead": len([q for q in st.q[:i] if q.sent]),
            "shares_ahead": len([q for q in ahead if set(named(q)) & set(nm)]),
        }

    plain_send = hold.send

    def watched_send(st):
        rows = [(send_row(st, c, i), c) for i, c in enumerate(st.q) if not c.sent]
        plain_send(st)
        for row, c in rows:
            ROWS["send-goes"].append((row, bool(c.sent)))

    plain_answer = fold.answer

    def watched_answer(st, good):
        sent = [i for i, c in enumerate(st.q) if c.sent]
        if sent:
            ROWS["answer-at"].append(({
                "qlen": len(st.q),
                "sent": len(sent),
                "unsent": len(st.q) - len(sent),
                "front_sent": int(st.q[0].sent),
                "front_kind": KIND[st.q[0].kind],
            }, sent[0]))
        at = sent[0] if sent else -1
        if sent and not good:
            c = st.q[at]
            after = st.q[at + 1:]
            nm = set(named(c))
            before = len(st.q)
            plain_answer(st, good)
            ROWS["take-count"].append(({
                "kind": KIND[c.kind],
                "after": len(after),
                "direct": len([q for q in after if set(named(q)) & nm]),
                "new_after": len([q for q in after if q.kind == "new"]),
                "qlen": before,
                "sent_after": len([q for q in after if q.sent]),
            }, before - len(st.q)))
            return
        plain_answer(st, good)

    plain_lay = lay.one

    def watched_lay(rec, c):
        if c.kind == "cut" and c.a in rec:
            kids = len([n for n, r in rec.items() if r.up == c.a])
            before = len(rec)
            plain_lay(rec, c)
            ROWS["cut-reach"].append(({
                "records": before,
                "kids": kids,
                "roots": len([n for n, r in rec.items() if r.up is None]),
                "named_top": int(rec.get(c.a) is None),
            }, before - len(rec)))
            return
        plain_lay(rec, c)

    hold.send = watched_send
    fold.answer = watched_answer
    lay.one = watched_lay
    view.lay = lay
    line.fold = fold

    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(10):
            r = random.Random("decide|%s|%d" % (fam, i))
            st = store.St()
            for op in scan.ops("\n".join(gen.build(fam, r, small=True))):
                step.run(st, op)
    return ROWS
