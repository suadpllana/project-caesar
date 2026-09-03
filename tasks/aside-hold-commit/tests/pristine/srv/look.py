from srv.mark import AO, AC, QO, QC


def read(raw):
    vis = bytearray()
    inert = bytearray()
    i = 0
    n = len(raw)
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
            i = j + len(o)
            continue
        vis += raw[plain:j]
        inert += bytes(j - plain)
        if kind:
            vis += raw[j:k + len(c)]
            inert += b"\x01" * (k + len(c) - j)
        i = k + len(c)
        plain = i
    vis += raw[plain:]
    inert += bytes(n - plain)
    return bytes(vis), bytes(inert)
