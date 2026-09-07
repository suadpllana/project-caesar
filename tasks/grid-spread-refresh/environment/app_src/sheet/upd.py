from sheet import store


def one(eng, ad):
    st = eng.st
    kind, vals, w = eng.calc(ad)
    if kind == "v":
        tgt = eng.ly.fit(st, ad, vals, w)
        if tgt is None:
            eng.ly.wipe(st, ad)
            st.show(ad, store.BLK)
        else:
            eng.ly.put(st, ad, vals, tgt)
            st.show(ad, vals[0] if vals else store.BLK)
    else:
        eng.ly.wipe(st, ad)
        st.show(ad, vals)
    eng.dp.note(ad, w.rd)
