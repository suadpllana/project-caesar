#!/bin/bash
# the answer computed the way it suggests itself: a bound on the rendering plus a per-byte state, and a stop window over that. Whether a byte is inert and what follows it are the same question asked twice, and merging the futures into one flag array throws that pairing away, so a stop looks reachable by taking a live reading of one byte together with a continuation that exists only in the world where the reading is inert.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/srv"
cat > "$APP/srv/hold.py" <<'AHC_EOF'
from srv import bite, look
from srv.mark import AO, AC, QO, QC

LIVE, INERT, MAYBE = 0, 1, 2
FAR = 1 << 30


def settled(raw):
    vis, inert = look.read(raw)
    bound = len(vis)
    flag = bytearray(INERT if b else LIVE for b in inert)
    for alt in (raw + AC, raw + QC, raw + AC + QC, raw + QC + AC,
                raw + AO[1:] + AC, raw + QO[1:] + QC):
        avis, ainert = look.read(alt)
        n = 0
        while n < bound and n < len(avis) and avis[n] == vis[n]:
            n += 1
        bound = n
        for p in range(n):
            if bool(ainert[p]) != bool(inert[p]):
                flag[p] = MAYBE
    return vis, bytes(flag), bound


def chop(vis, flag, bound, stops):
    sure = FAR
    risk = FAR
    for at in range(bound):
        for st in stops:
            reach = at + len(st)
            if reach <= bound:
                if vis[at:reach] != st:
                    continue
                part = flag[at:reach]
                if all(f == LIVE for f in part):
                    if at < sure:
                        sure = at
                elif all(f != INERT for f in part):
                    if at < risk:
                        risk = at
            elif st.startswith(vis[at:bound]):
                if all(f != INERT for f in flag[at:bound]) and at < risk:
                    risk = at
    keep = min(bound, risk, sure)
    return keep, sure < FAR and sure <= risk and sure == keep


def ready(st):
    if st.ended:
        vis, inert = look.read(st.raw)
        text, tin, _ = bite.chop(vis, inert, st.stops)
        st.box["seen"] = [(text, tin)]
        return text, True
    vis, flag, bound = settled(st.raw)
    keep, fin = chop(vis, flag, bound, st.stops)
    st.box["seen"] = [(vis[:keep], bytes(1 if f == INERT else 0 for f in flag[:keep]))]
    return vis[:keep], fin
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
