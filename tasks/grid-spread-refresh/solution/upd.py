"""Reference single-cell update.

One recomputation: evaluate through the engine, decide the block layout, write the
displayed values, and replace the cell's read record. The cells whose displayed value
actually moved are returned, and they are the only reason to look at anybody else. The
set is collected from the cells this recomputation can write - the cell itself, the block
it held and the block it now holds - and their values are read before anything is written.
"""

from sheet import store


def one(eng, ad):
    st = eng.st
    kind, vals, w = eng.calc(ad)
    tgt = eng.ly.fit(st, ad, vals, w) if kind == "v" else None
    watch = set(eng.ly.fp.get(ad, ()))
    if tgt:
        watch.update(tgt)
    watch.add(ad)
    was = dict((t, st.val(t)) for t in watch)
    if kind != "v":
        eng.ly.wipe(st, ad)
        st.show(ad, vals)
    elif tgt is None:
        eng.ly.wipe(st, ad)
        st.show(ad, store.BLK)
    else:
        eng.ly.put(st, ad, vals, tgt)
        st.show(ad, vals[0] if vals else None)
    eng.dp.note(ad, w.rd)
    return [t for t in watch if st.val(t) != was[t]]
