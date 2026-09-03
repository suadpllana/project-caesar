#!/bin/bash
# the futures are taken to part company where they structurally diverge, at the opener. Two renderings can differ from that point and still agree on the byte there, because the byte the one that hides an aside moves up into the slot can be the byte the other one shows.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/srv"
cat > "$APP/srv/hold.py" <<'AHC_EOF'
from srv import bite, look
from srv.mark import AO, AC, QO, QC


def _bound(raw):
    i = 0
    n = len(raw)
    shown = 0
    plain = 0
    while i < n:
        ja = raw.find(AO, i)
        jq = raw.find(QO, i)
        opts = []
        if ja >= 0:
            opts.append((ja, 0, AO, AC))
        if jq >= 0:
            opts.append((jq, 1, QO, QC))
        if not opts:
            break
        j, kind, o, c = min(opts)
        k = raw.find(c, j + len(o))
        if k < 0:
            return shown + (j - plain)
        shown += j - plain
        if kind:
            shown += k + len(c) - j
        i = k + len(c)
        plain = i
    return shown + (n - plain)


def ready(st):
    vis, inert = look.read(st.raw)
    if st.ended:
        text, tin, _ = bite.chop(vis, inert, st.stops)
        st.box["seen"] = [(text, tin)]
        return text, True
    bound = _bound(st.raw)
    wide = 0
    for s in st.stops:
        if len(s) - 1 > wide:
            wide = len(s) - 1
    keep = max(0, min(bound, len(vis)) - wide)
    text, tin, hit = bite.chop(vis[:keep], inert[:keep], st.stops)
    st.box["seen"] = [(text, tin)]
    return text, hit
AHC_EOF
cat > "$APP/srv/pick.py" <<'AHC_EOF'
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
    seen = st.box.get("seen") or ()
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
AHC_EOF
