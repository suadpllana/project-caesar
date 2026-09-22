import sys

from db import audit, drop, parse, rows, say


def main(path):
    script = parse.read(path)
    store = rows.Store(script)
    for tab, rid, vals in script.rows:
        store.add(tab.name, rid, vals)
    out = sys.stdout
    for st in script.stmts:
        if st.op == "delete":
            lines = [say.verdict(drop.delete(store, st.tab.name, st.ids))]
        elif st.op == "dump":
            lines = say.dump(store, st.tab.name)
        else:
            lines = say.audit(audit.audit(store))
        for line in lines:
            out.write(line + "\n")
    out.flush()


if __name__ == "__main__":
    main(sys.argv[1])
