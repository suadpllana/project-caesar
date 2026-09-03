"""A second implementation of the same specification, written from the specification.

It shares no code with the tree under /app and it does not reproduce its shape. Where the
reference decides what is settled by carrying a per-byte state and a bound, this one renders
whole worlds and intersects them: it builds the small set of futures that can still change the
answer, renders each one to the end with a left-to-right state machine, and keeps what they
all agree on. The two therefore agree only if the specification, and not one author's way of
walking it, is what produced the answer.

Rendering here is a state machine over the bytes, driven by two lookahead tables that say
where the next closer of each kind begins. The reference walks the string with find(). The
witness set is the second difference: closing an opener takes a closer that may not overlap
it, so a world that closes a trailing '<' has to spell out the opener first.
"""

AO, AC = b"<~", b"~>"
QO, QC = b"<#", b"#>"
OUT, ASIDE, QUOTE = 0, 1, 2


def _after(raw, mark):
    """after[i] is the least j >= i at which mark starts, or len(raw) when there is none."""
    n = len(raw)
    out = [n] * (n + 1)
    for i in range(n - 1, -1, -1):
        out[i] = i if raw[i:i + len(mark)] == mark else out[i + 1]
    return out


def render(raw):
    """(visible bytes, inert flags) for a stream that has stopped.

    An opener whose closer never arrives is ordinary text, and the scan carries on from just
    past it, so a later bracket of the other kind can still form.
    """
    n = len(raw)
    na, nq = _after(raw, AC), _after(raw, QC)
    vis, inert = bytearray(), bytearray()
    state, at, shut = OUT, 0, 0
    while at < n:
        if state == OUT:
            is_a = raw[at:at + 2] == AO
            is_q = raw[at:at + 2] == QO
            if is_a and na[at + 2] < n:
                state, shut = ASIDE, na[at + 2]
                at += 2
                continue
            if is_q and nq[at + 2] < n:
                state, shut = QUOTE, nq[at + 2]
                vis += raw[at:at + 2]
                inert += b"\x01\x01"
                at += 2
                continue
            vis.append(raw[at])
            inert.append(0)
            at += 1
            continue
        if at == shut:
            if state == QUOTE:
                vis += raw[at:at + 2]
                inert += b"\x01\x01"
            state = OUT
            at += 2
            continue
        if state == QUOTE:
            vis.append(raw[at])
            inert.append(1)
        at += 1
    return bytes(vis), bytes(inert)


def clip(vis, inert, stops):
    """Cut at the earliest stop no byte of which is inert. Returns (text, ended_on_a_stop)."""
    best = None
    for st in stops:
        at = 0
        while True:
            at = vis.find(st, at)
            if at < 0:
                break
            if not any(inert[at:at + len(st)]):
                if best is None or at < best:
                    best = at
                break
            at += 1
    if best is None:
        return vis, inert, False
    return vis[:best], inert[:best], True


def calls(vis, inert):
    out, i, n = [], 0, len(vis)
    while i < n:
        if vis[i:i + 1] == b"{":
            j = vis.find(b"}", i + 1)
            if j > i and not any(inert[i:j + 1]):
                nm = vis[i + 1:j]
                if nm and all(97 <= b <= 122 for b in nm):
                    out.append(nm.decode())
                    i = j + 1
                    continue
        i += 1
    return out


def _tails(stops):
    """Every nonempty proper prefix-completing suffix a stop could still need."""
    out = {b""}
    for st in stops:
        for k in range(1, len(st) + 1):
            out.add(st[k:])
            out.add(st)
    out.discard(b"")
    return sorted(out)


def worlds(raw, stops):
    """Futures that can still move the answer.

    Closing an opener that is already whole takes its closer. Closing a trailing '<' takes the
    second byte of an opener first, because a closer may not overlap the opener it shuts. On
    top of each of those, any suffix that finishes a stop already begun, and a filler byte
    that finishes nothing.
    """
    heads = [b"", AC, QC, b"~" + AC, b"#" + QC, AO[1:] + AC, QO[1:] + QC]
    tails = [b""] + _tails(stops) + [b"a"]
    out = []
    for h in heads:
        for t in tails:
            out.append(raw + h + t)
    return out


def agree(raw, stops):
    """What every possible continuation already agrees about.

    Returns (text, names, done): the client text they all share, the calls they all already
    carry in the same order, and whether no continuation adds anything at all. A call is a
    side effect that cannot be taken back, so it waits for the same agreement the text does -
    a call the model has written inside a quote that has not closed yet is a call in some
    worlds and quoted text in others, and neither answer may be acted on.
    """
    texts, lists = [], []
    for w in worlds(raw, stops):
        vis, inert = render(w)
        text, tinert, _ = clip(vis, inert, stops)
        texts.append(text)
        lists.append(calls(text, tinert))
    keep = texts[0]
    for text in texts[1:]:
        n = 0
        while n < len(keep) and n < len(text) and keep[n] == text[n]:
            n += 1
        keep = keep[:n]
    names = lists[0]
    for lst in lists[1:]:
        n = 0
        while n < len(names) and n < len(lst) and names[n] == lst[n]:
            n += 1
        names = names[:n]
    return keep, names, all(t == keep for t in texts)


def sure(raw, stops):
    keep, _, done = agree(raw, stops)
    return keep, done


def ready(raw, stops, ended):
    if ended:
        vis, inert = render(raw)
        text, tinert, _ = clip(vis, inert, stops)
        return text, calls(text, tinert), True
    return agree(raw, stops)


def answer(name):
    v = 0
    for b in name.encode():
        v = (v * 33 + b) % 211
    return "hi" if v % 2 else "lo"


def drive(job):
    """Replay the run the server makes when its timing is right."""
    stops = job["stops"]
    scripts = job["scripts"]
    turns = job["turns"]
    cur, at, raw = "s0", 0, b""
    out, tr, done = b"", [], []
    step = 0
    while step < 400:
        if at >= len(scripts[cur]):
            break
        step += 1
        tok = scripts[cur][at]
        at += 1
        raw += tok
        tr.append(["tk", step, tok.decode("latin1")])
        sent, names, fin = ready(raw, stops, False)
        if len(sent) > len(out):
            tr.append(["ch", step, sent[len(out):].decode("latin1")])
            out = sent
        for nm in names[len(done):]:
            done.append(nm)
            val = answer(nm)
            tr.append(["dp", step, nm, val])
            key = cur + "|" + val
            if key in turns:
                cur, at = turns[key], 0
                tr.append(["br", step, cur])
        if fin:
            tr.append(["fi", step])
            break
    sent, names, _ = ready(raw, stops, True)
    if len(sent) > len(out):
        tr.append(["ch", step, sent[len(out):].decode("latin1")])
        out = sent
    for nm in names[len(done):]:
        done.append(nm)
        tr.append(["dp", step, nm, answer(nm)])
    tr.append(["en", out.decode("latin1"), len(done)])
    return tr
