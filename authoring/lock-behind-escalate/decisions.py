"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: how many other
transactions hold a conflicting record, how many earlier waiting requests conflict, how many
requests are waiting at all, the transaction's row records on the table, the threshold, the
records held. Nothing says which waiters depend on the requester, because the shipped tree
has no notion of it and building one is the work.

The verdict to want is that at least one graded quantity has no short rule. The one that
should not have one is whether a request that no holder blocks is granted, because the
answer depends on reachability over the wait relation; whether an escalation is taken should
not either, for the same reason. Whether a request is covered is a stated rule with nothing
hidden and should come out short.

The watched copies below mirror the reference and are asserted to reproduce the sealed
model's trace on every script, so a copy that drifted cannot quietly report on a different
engine.

    python3 tools/onelinecheck.py lock-behind-escalate
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"soft-blocked": [], "escalate": [], "covered": [], "victim-is-oldest": []}


def _install(here):
    sys.path.insert(0, str(here))
    for name in [n for n in sys.modules if n == "run_lm" or n == "lm" or n.startswith("lm.")]:
        del sys.modules[name]
    import run_lm
    from lm import dead, esc, grant, settle, spec
    return run_lm, dead, esc, grant, settle, spec


def _watch(dead, esc, grant, settle, spec):
    real_grantable = grant.grantable
    real_after_row = esc.after_row
    real_victim = dead.victim
    real_lock = settle.Mgr.lock

    def grantable(held, wait, txn, tgt, mode, seq, view=None):
        got = real_grantable(held, wait, txn, tgt, mode, seq, view)
        holders = len(set(held.clashers(txn, tgt, mode)))
        earlier = sum(1 for w in wait.clashing(tgt, mode) if w.txn != txn and w.seq < seq)
        if holders == 0 and seq != grant.LATEST:
            ROWS["soft-blocked"].append(({
                "earlier": earlier, "waiting": len(wait.queue),
                "held": held.count(txn), "row": int(spec.is_row(tgt)),
            }, got))
        return got

    def after_row(mgr, txn, table):
        rows = mgr.held.rows(txn, table)
        before = len(mgr.out.lines)
        real_after_row(mgr, txn, table)
        if len(rows) >= mgr.cfg.k:
            others = len({u for u, _r in mgr.held.others(txn, table)}) \
                if hasattr(mgr.held, "others") else len(mgr.held.tab.get(table, {})) - \
                (1 if txn in mgr.held.tab.get(table, {}) else 0)
            waiting = sum(1 for w in mgr.wait.queue if spec.table_of(w.tgt) == table)
            ROWS["escalate"].append(({
                "rows": len(rows), "k": mgr.cfg.k, "others": others, "waiting": waiting,
                "xrows": sum(1 for _t, m in rows if m == "x"),
            }, len(mgr.out.lines) > before))

    def lock(self, txn, tgt, mode):
        rs = self.held.rec[txn]
        same = rs.get(tgt)
        table = rs.get(spec.table_of(tgt))
        ROWS["covered"].append(({
            "same_x": int(same == "x"), "same_s": int(same == "s"),
            "table_x": int(table == "x"), "table_s": int(table == "s"),
            "want_x": int(mode == "x"), "row": int(spec.is_row(tgt)),
        }, self.held.covered(txn, tgt, mode)))
        real_lock(self, txn, tgt, mode)

    def victim(held, wait):
        v = real_victim(held, wait)
        if v is not None:
            cyclic = dead.on_cycles(dead.hard_edges(held, wait))
            oldest = min(cyclic, key=lambda t: int(t[1:]))
            ROWS["victim-is-oldest"].append(({
                "n": len(cyclic), "held_min": min(held.count(t) for t in cyclic),
                "held_max": max(held.count(t) for t in cyclic),
            }, v == oldest))
        return v

    grant.grantable = grantable
    esc.after_row = after_row
    dead.victim = victim
    settle.Mgr.lock = lock


def samples():
    here = lab.tree(lab.SOL)
    run_lm, dead, esc, grant, settle, spec = _install(here)
    _watch(dead, esc, grant, settle, spec)

    _cases, gen, model = lab.sealed()
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(10):
            rng = random.Random("decide|%s|%d" % (fam, i))
            lines = gen.build(fam, rng)
            got = run_lm.run("\n".join(lines) + "\n")
            assert got == model.expect(lines), \
                "the watched copy drifted from the contract on %s-%d" % (fam, i)
    return ROWS


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        kinds = len({str(y) for _r, y in rows})
        print("%-18s %d rows, %d outcomes" % (name, len(rows), kinds))
