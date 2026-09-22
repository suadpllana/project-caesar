"""The graded decisions as rows of features the agent can actually read. Never ships.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
ones the shipped tree exposes at that moment: the rows, the modes in force, the statement, and
anything a scan of the rows gives - which rows violate a deferred constraint now, which parent
keys are left behind now, and where they fall in scan order. The owed ledger is not offered,
because the shipped tree has none; that it is history rather than a function of the rows is the
task.

Four questions are asked. Whether a check point raises is expected to have a short rule, since a
violation that exists now is owed by some entry either way. Which entry it names, how many
entries a statement adds, and how many a rollback to a savepoint brings back should not.

    python3 authoring/owed-check-rewind/decisions.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, model = lab.sealed()


def _violations(cat, heap, mode, names=None):
    """What a scan of the rows sees now: deferred constraints in declaration order, violating
    child rows in key order, then left-behind parent keys in key order."""
    out = []
    for con in cat.cons:
        if mode.get(con.name) != "d" or (names is not None and con.name not in names):
            continue
        pos = cat.tables[con.table].pos[con.col]
        rows = heap.t[con.table]
        for k in sorted(rows):
            v = rows[k][pos]
            if con.kind == "check":
                bad = v is None if con.test == "notnull" else (v is not None and v < con.floor)
            else:
                bad = v is not None and v not in heap.t[con.parent]
            if bad:
                out.append((con.name, con.table, k))
        if con.kind == "fk":
            held = sorted({row[pos] for row in rows.values() if row[pos] is not None})
            for k in held:
                if k not in heap.t[con.parent]:
                    out.append((con.name, con.parent, k))
    return out


def _covered(cat, st):
    if st.op == "commit":
        return None
    if st.name == "all":
        return {c.name for c in cat.cons if c.deferrable}
    return {st.name}


def samples():
    raises, names, adds, backs = [], [], [], []
    for seed in ("decisions0", "decisions1"):
        for fam, _name, lines in gen.programs(seed, 12):
            if fam in ("wrap", "load"):
                continue
            mod = lab.inproc(lab.tree(policy=lab.SOL))
            text = "\n".join(lines) + "\n"
            p = mod.prog.load(text)
            s = mod.sess.Session(p.cat, p.rows)
            cat = p.cat
            for st in p.stmts:
                before = _violations(cat, s.heap, s.mode) if s.mode else []
                if st.op in ("set", "commit") and not s.dead and \
                        (st.op == "commit" or st.want == "immediate") and \
                        (st.op == "commit" or st.name == "all" or cat.con(st.name).deferrable):
                    cover = _covered(cat, st)
                    scan = _violations(cat, s.heap, s.mode, cover)
                    rows_bad = sum(1 for e in scan if e[1] == cat.con(e[0]).table)
                    out = s.step(st)
                    raises.append(({
                        "scan_violations": len(scan),
                        "scan_rows": rows_bad,
                        "scan_keys": len(scan) - rows_bad,
                        "covered_constraints": len(cover) if cover is not None else len(cat.cons),
                        "is_commit": int(st.op == "commit"),
                    }, out[0] == "raise"))
                    if out[0] == "raise":
                        named = tuple(out[1:4])
                        first_key = next((i for i, e in enumerate(scan)
                                          if e[1] != cat.con(e[0]).table), -1)
                        names.append(({
                            "first_scanned": 0 if scan else -1,
                            "last_scanned": len(scan) - 1,
                            "first_key_scanned": first_key,
                            "scan_violations": len(scan),
                        }, scan.index(named) if named in scan else -1))
                    continue
                if st.op in ("insert", "update", "delete") and not s.dead:
                    out = s.step(st)
                    if out[0] != "ok":
                        continue
                    after = _violations(cat, s.heap, s.mode)
                    new = [e for e in after if e not in before]
                    new_rows = sum(1 for e in new if e[1] == cat.con(e[0]).table)
                    adds.append(({
                        "new_violations": len(new),
                        "new_violating_rows": new_rows,
                        "new_left_behind_keys": len(new) - new_rows,
                        "gone_violations": sum(1 for e in before if e not in after),
                        "violations_after": len(after),
                        "stmt_kind": {"insert": 1, "update": 2, "delete": 3}[st.op],
                    }, len(out[2])))
                    continue
                if st.op == "back":
                    out = s.step(st)
                    if out[0] != "ok":
                        continue
                    after = _violations(cat, s.heap, s.mode)
                    backs.append(({
                        "violations_before": len(before),
                        "violations_after": len(after),
                        "reappeared": sum(1 for e in after if e not in before),
                        "vanished": sum(1 for e in before if e not in after),
                    }, len(out[2])))
                    continue
                s.step(st)
    return {
        "check point raises": raises,
        "check point names (scan index)": names,
        "statement adds (count)": adds,
        "rollback to brings back (count)": backs,
    }


if __name__ == "__main__":
    for q, rows in samples().items():
        print("%-34s %5d samples, %d outcomes" % (q, len(rows), len({str(y) for _, y in rows})))
