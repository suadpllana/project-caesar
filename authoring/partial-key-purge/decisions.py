"""The graded decisions as rows of features the agent can read. Authoring only.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are raw
ones a solver can read off the store at the moment of the decision without having solved
anything: how many rows a row matches through its cascade reference, whether the deleted row is
among them, whether the row matches itself, how many cascade, restrict, noaction and setnull
references point at a row, how many live cascade references a row has. Nothing derived from the
removal rule is offered, because the derivation is the task.

Four questions, labelled by the reference:
  removed-by-lone-delete   is row v removed when row r alone is deleted (every pair in a store)
  audit-removed            how many rows a lone delete of r removes
  audit-held               whether a lone delete of r is refused
  delete-refused           whether a delete statement of a generated script is refused

    python3 authoring/partial-key-purge/decisions.py
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agree  # noqa: E402
import gen  # noqa: E402

APP = None


def _load():
    global APP
    if APP is None:
        APP = agree.tree_for(os.path.join(agree.TASK, "solution"))
        sys.path.insert(0, APP)
    from db import audit, drop, match, parse, rows
    return audit, drop, match, parse, rows


def _store(text):
    audit, drop, match, parse, rows = _load()
    script = parse.parse(text)
    store = rows.Store(script)
    for tab, rid, vals in script.rows:
        store.add(tab.name, rid, vals)
    return script, store


def _raw(store, match):
    """Per row: its cascade match set and the counts of references pointing at it."""
    bk = match.book(store)
    cas, pointed = {}, {}
    for tab in store.script.tabs:
        for rid in store.ids(tab.name):
            vals = store.get(tab.name, rid)
            live = 0
            for ref in tab.refs:
                ms = [(ref.key.tab.name, p) for p in bk.ups(ref, vals)]
                for m in ms:
                    pointed.setdefault(m, {}).setdefault(ref.act, 0)
                    pointed[m][ref.act] += 1
                if ref.act == "cascade" and ms:
                    live += 1
                    cas.setdefault((tab.name, rid), []).extend(ms)
            cas.setdefault((tab.name, rid), [])
            pointed.setdefault((tab.name, rid), {})
            pointed[(tab.name, rid)]["live"] = live
    return cas, pointed


def samples():
    audit_m, drop, match, parse, rows = _load()
    out = {"removed-by-lone-delete": [], "audit-removed": [], "audit-held": [],
           "delete-refused": []}
    for i in range(160):
        fam = gen.SMALL[i % len(gen.SMALL)]
        rng = random.Random("decisions:%s:%d" % (fam, i))
        text = gen.abstract(rng) if fam == "mixed" else gen.story(rng, fam)
        script, store = _store(text)
        cas, pointed = _raw(store, match)
        for t, r, gone, wiped, held in audit_m.audit(store):
            p = pointed[(t, r)]
            feats = {"cascade_in": p.get("cascade", 0), "restrict_in": p.get("restrict", 0),
                     "noaction_in": p.get("noaction", 0), "setnull_in": p.get("setnull", 0),
                     "live_cascade": p["live"], "matches": len(cas[(t, r)]),
                     "self": int((t, r) in cas[(t, r)])}
            out["audit-removed"].append((feats, gone))
            out["audit-held"].append((feats, bool(held)))
            if len(out["removed-by-lone-delete"]) < 6000:
                eff = drop.plan(store, t, [r])
                for v, ms in cas.items():
                    if v == (t, r):
                        continue
                    f2 = {"v_matches": len(ms), "v_matches_r": int((t, r) in ms),
                          "v_self": int(v in ms), "v_live_cascade": pointed[v]["live"],
                          "r_cascade_in": p.get("cascade", 0)}
                    out["removed-by-lone-delete"].append((f2, v in eff.gone))
        for st in script.stmts:
            if st.op != "delete":
                continue
            if not all(store.has(st.tab.name, rid) for rid in st.ids):
                break
            p = [pointed[(st.tab.name, rid)] for rid in st.ids]
            feats = {"named": len(st.ids), "restrict_in": sum(x.get("restrict", 0) for x in p),
                     "noaction_in": sum(x.get("noaction", 0) for x in p),
                     "setnull_in": sum(x.get("setnull", 0) for x in p),
                     "cascade_in": sum(x.get("cascade", 0) for x in p)}
            res = drop.delete(store, st.tab.name, st.ids)
            out["delete-refused"].append((feats, res[0] == "refused"))
            cas, pointed = _raw(store, match)
            break
    return out


if __name__ == "__main__":
    for name, rows_ in samples().items():
        yes = sum(1 for _, y in rows_ if y is True)
        print(name, len(rows_), "samples", yes if yes else "")
