def resolve(img, line):
    found = {}
    for r in img.rows:
        if r.line != line:
            continue
        f = img.fn_at(r.at)
        if f.name not in found or r.at < found[f.name]:
            found[f.name] = r.at
    return sorted(found.values())
