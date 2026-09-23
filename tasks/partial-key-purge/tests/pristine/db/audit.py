import copy

from db import drop, rows


def audit(store):
    out = []
    for tab in store.script.tabs:
        for rid in store.ids(tab.name):
            twin = rows.Store(store.script)
            twin.data = copy.deepcopy(store.data)
            res = drop.delete(twin, tab.name, [rid])
            if res[0] == "ok":
                out.append((tab.name, rid, res[1], res[2], None))
            else:
                out.append((tab.name, rid, 0, 0, (res[1], res[2])))
    return out
