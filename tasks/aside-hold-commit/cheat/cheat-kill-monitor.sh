#!/bin/bash
# switches the instrumentation off from inside a decision, once the run is going. An import-time attempt is a no-op, because the runner arms after it imports the tree. Built on the reference, so its answers are all correct and the only thing that can reject it is the layer it is aimed at.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/srv"
cat > "$APP/srv/hold.py" <<'AHC_EOF'
import sys as _sys


def _quiet():
    try:
        mon = getattr(_sys, "monitoring", None)
        if mon is not None:
            mon.set_events(3, 0)
            mon.free_tool_id(3)
        else:
            _sys.setprofile(None)
    except Exception:
        pass


from srv import bite, look
from srv.mark import AO, AC, QO, QC

# The whole question is which futures can still change what has already been rendered, and
# there are only two of those: the aside opener that is waiting for a closer, and the quote
# opener that is. Each is settled by its own closer, and a closer may not overlap the opener it
# shuts, so a trailing '<' needs the second byte of an opener spelled out before a closer can
# follow. On top of each of those, whatever would finish a stop the text has already begun,
# and one byte that finishes nothing - the last is what says the response is not over yet.
HEADS = (b"", AC, QC, AO[1:] + AC, QO[1:] + QC)


def _tails(stops):
    out = {b"a"}
    for st in stops:
        for k in range(len(st)):
            out.add(st[k:])
    return sorted(out)


def _futures(raw, stops):
    tails = [b""] + _tails(stops)
    return [raw + head + tail for head in HEADS for tail in tails]


def _shared(texts):
    keep = texts[0]
    for text in texts[1:]:
        n = 0
        while n < len(keep) and n < len(text) and keep[n] == text[n]:
            n += 1
        keep = keep[:n]
    return keep


def ready(st):
    """The prefix of the response that cannot come out any other way, and whether it is all.

    Nothing may be sent that some continuation would not have sent, and everything that every
    continuation sends has to go now, so the answer is the intersection of the finished
    responses the still-open futures would produce.

    It is worth saying why this is not a bound on the rendering plus a window for a stop, which
    is the shape that suggests itself and is wrong. Whether a byte is inert and what follows it
    are the same question asked twice: the byte in front of an open quote is live only in the
    future where that quote never closes, and in that future what comes after it is already
    fixed. Carrying inertness as a per-byte state throws that pairing away, and a stop then
    looks reachable by taking a live reading of one byte together with a continuation that only
    exists in the world where the reading is inert. So the futures have to be kept whole.
    """
    _quiet()
    if st.ended:
        vis, inert = look.read(st.raw)
        done = [bite.chop(vis, inert, st.stops)[:2]]
        st.box["seen"] = done
        return done[0][0], True
    seen = []
    for future in _futures(st.raw, st.stops):
        vis, inert = look.read(future)
        text, tin, _ = bite.chop(vis, inert, st.stops)
        seen.append((text, tin))
    st.box["seen"] = seen
    keep = _shared([text for text, _ in seen])
    return keep, all(text == keep for text, _ in seen)
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
