def pick(f, ch):
    hits = [i for i, g in enumerate(ch) if g.hit]
    if not hits:
        return None
    guards = [i for i, g in enumerate(ch) if g.sh]
    lo = guards[-1] if guards else 0
    keep = [i for i in hits if i >= lo]
    return ch[min(keep)] if keep else None
