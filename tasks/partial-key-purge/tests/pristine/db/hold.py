from db import match


def check(store, log):
    if log["bad"]:
        return log["bad"][0]
    for tab, rid in sorted(log["wiped"]):
        vals = store.get(tab, rid)
        for ref in store.tabs[tab].refs:
            if match.form(ref, vals) and not match.ups(store, ref, vals):
                return (ref.name, rid)
    return None
