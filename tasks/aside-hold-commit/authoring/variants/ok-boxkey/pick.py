def _names(text, inert, limit):
    out = []
    i = 0
    n = min(len(text), limit)
    while i < n:
        if text[i:i + 1] == b"{":
            j = text.find(b"}", i + 1)
            if 0 < j < n and not any(inert[i:j + 1]):
                nm = text[i + 1:j]
                if nm and all(97 <= b <= 122 for b in nm):
                    out.append(nm.decode())
                    i = j + 1
                    continue
        i += 1
    return out


def take(st, sent):
    """The calls the response certainly carries, in order.

    A call is a side effect that cannot be taken back, so it waits for the same agreement the
    text does, and it needs its own intersection rather than a reading off the text that was
    sent. A call the model wrote inside a quote that has not closed is a call in the future
    where the quote never closes and quoted text in the one where it does; the bytes are the
    same either way, so the text can be sent while the call still cannot be made.

    hold.ready leaves the futures it rendered where they can be read, because rendering them
    twice would be the same work for the same answer.
    """
    seen = st.box.get("~~carry~~") or ()
    if not seen:
        return ()
    lists = [_names(text, inert, len(sent)) for text, inert in seen]
    names = lists[0]
    for lst in lists[1:]:
        n = 0
        while n < len(names) and n < len(lst) and names[n] == lst[n]:
            n += 1
        names = names[:n]
    return tuple(names)
