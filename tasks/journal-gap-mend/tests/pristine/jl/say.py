def text(entry):
    if entry.kind == "beat":
        return "beat %d" % entry.sess
    return "%s %d %d %s" % (entry.kind, entry.lock, entry.sess, entry.out)


def span(n, restored, cands):
    lines = ["gap %d" % n]
    lines.extend(text(e) for e in restored)
    if cands:
        lines.append("? " + " | ".join(sorted("-" if c is None else text(c) for c in cands)))
    return lines
