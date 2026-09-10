from base import box, text
import ops


def clean(raw):
    out = []
    for row in raw:
        row = row.split("#")[0].strip()
        if row:
            out.append(row)
    return out


def run(raw):
    rows = clean(raw)
    acc = []
    head = rows[0].split()
    blocks = int(head[1])
    st = box.Store(blocks)
    acc.append(text.dev(blocks))
    for row in rows[1:]:
        ops.ex(st, tuple(row.split()), acc)
    return acc
