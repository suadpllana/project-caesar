def sweep(tb, now, horizon):
    if horizon <= 0 or len(tb.items) <= horizon:
        return
    tb.items.sort(key=lambda st: st.mark)
    del tb.items[:len(tb.items) - horizon]
