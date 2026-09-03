from srv import bite, look
from srv.mark import AO, AC, QO, QC

# The whole question is which futures can still change what has already been rendered, and
# there are only two of those: the aside opener that is waiting for a closer, and the quote
# opener that is. Each is settled by its own closer, and a closer may not overlap the opener it
# shuts, so a trailing '<' needs the second byte of an opener spelled out before a closer can
# follow. On top of each of those, whatever would finish a stop the text has already begun,
# and one byte that finishes nothing - the last is what says the response is not over yet.
HEADS = (b"", AC, QC, AC + QC, QC + AC, AO[1:] + AC, QO[1:] + QC,
         AC + AC, QC + QC, AO[1:] + AC + QC, QO[1:] + QC + AC, AC + QC + AC)


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
