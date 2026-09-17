def shelf(tag, ident, up, fld):
    parts = [tag, ident, up]
    for k in sorted(fld):
        parts.append("%s=%d" % (k, fld[k]))
    return " ".join(parts)


def wire(tag, kind, ident):
    return "%s %s %s" % (tag, kind, ident)
