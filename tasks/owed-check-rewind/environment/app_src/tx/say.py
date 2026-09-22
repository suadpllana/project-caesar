def line(out):
    kind = out[0]
    if kind == "ok":
        parts = ["ok"]
        parts.extend("-%s %s %d" % e for e in out[1])
        parts.extend("+%s %s %d" % e for e in out[2])
        return " ".join(parts)
    if kind == "raise":
        return "raise %s %s %d" % tuple(out[1:4])
    return kind
