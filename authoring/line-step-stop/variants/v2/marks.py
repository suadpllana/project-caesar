# Correct variant V2: group statement rows of the line by their innermost scope.
from dbg.frames import tree


def resolve(img, line):
    t = tree(img)
    per = {}
    for r in img.rows:
        if r.stmt and r.line == line:
            owner = t.scopes(r.at)[-1]
            per.setdefault(id(owner), []).append(r.at)
    return sorted(min(v) for v in per.values())
