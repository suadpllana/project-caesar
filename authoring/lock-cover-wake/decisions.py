"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: the mode asked for, the
modes that transaction already holds on the resource and on its table, the begin positions of
the asker and the holder, what the entry in front of them holds and how long its queue is, the
row count on the table and the limit. Nothing says what a holder is standing under, because the
shipped tree has no such field and building one is part of the work; nothing says which rows a
table grant is about to take away, for the same reason.

The verdict to want is that at least one graded quantity has no short rule. The felling decision
should not: what decides it is the earliest begin waiting on the holder's *other* entries, which
is not a value any row here carries. The raise should be short - it is a stated threshold with
nothing hidden behind it, and `cheat-esc-over`, `cheat-esc-queues` and `cheat-esc-fells` cover
the readings that get it wrong.

The wrapped copies below call the reference and are asserted against the sealed model, so a
wrapper that drifted cannot quietly report on a different engine.

    python3 tools/onelinecheck.py lock-cover-wake
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

CODE = {None: 0, "IS": 1, "IX": 2, "S": 3, "SIX": 4, "X": 5}

ROWS = {"covered": [], "fell": [], "raise": [], "subsume": []}


def _install(here):
    sys.path.insert(0, str(here))
    for name in [n for n in sys.modules if n == "run_lk" or n == "lk" or n.startswith("lk.")]:
        del sys.modules[name]
    import run_lk
    from lk import ask, lift, mode, read, txn
    return run_lk, ask, lift, mode, read, txn


def _watch(ask, lift, mode, read, txn):
    real_ask = ask.Engine.ask
    real_place = ask.Engine.place
    real_lift = lift.lift
    real_subsume = lift.subsume

    def watched_ask(self, t, res, m):
        tbl, row = read.split_res(res)
        own = t.held.get(res)
        top = t.held.get(str(tbl)) if row >= 0 else None
        before = self.cov
        real_ask(self, t, res, m)
        ROWS["covered"].append(({
            "asked": CODE[m], "own": CODE[own], "top": CODE[top], "isrow": 1 if row >= 0 else 0,
        }, 1 if self.cov > before else 0))

    def watched_place(self, t, res, tgt, cont):
        e = self.ents.get(res)
        if e is not None:
            for tid in sorted(e.foes(t.tid, tgt), key=lambda k: self.txns[k].seq):
                h = self.txns[tid]
                ROWS["fell"].append(({
                    "mine": t.seq, "his": h.seq, "hisheld": len(h.held),
                    "queued": len(e.cq) + len(e.nq),
                    "hereold": -1 if e.old is None else e.old,
                    "hismode": CODE[e.held.get(tid)], "asked": CODE[tgt],
                }, 1 if h.state != "cut" and _will_fell(self, t, h, res, txn) else 0))
        real_place(self, t, res, tgt, cont)

    def watched_lift(eng, t, tbl):
        bag = t.rows.get(tbl) or {}
        res = str(tbl)
        e = eng.ents.get(res)
        cur = t.held.get(res)
        want = "S" if all(v == "S" for v in bag.values()) else "X"
        tgt = mode.cover(cur, want)
        before = len(eng.out)
        real_lift(eng, t, tbl)
        ROWS["raise"].append(({
            "tally": len(bag), "esc": eng.esc,
            "alls": 1 if all(v == "S" for v in bag.values()) else 0,
            "blocked": 1 if (e is not None and e.hits_but(t.tid, tgt)) else 0,
        }, 1 if len(eng.out) > before else 0))

    def watched_subsume(eng, t, tbl, m):
        bag = dict(t.rows.get(tbl) or {})
        real_subsume(eng, t, tbl, m)
        left = t.rows.get(tbl) or {}
        ROWS["subsume"].append(({
            "mode": CODE[m], "rows": len(bag),
            "sof": sum(1 for v in bag.values() if v == "S"),
            "xof": sum(1 for v in bag.values() if v == "X"),
        }, len(bag) - len(left)))

    ask.Engine.ask = watched_ask
    ask.Engine.place = watched_place
    lift.lift = watched_lift
    lift.subsume = watched_subsume


def _will_fell(eng, t, h, res, txn):
    return t.seq < txn.standing(h, res, eng.ents)


def samples():
    cases, gen, model = lab.sealed()
    here = lab.tree(policy=str(lab.SOL))
    run_lk, ask, lift, mode, read, txn = _install(here)
    _watch(ask, lift, mode, read, txn)

    work = [cases.prog(name) for name in cases.ORDER]
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(10):
            work.append(gen.build(fam, random.Random("decide|%s|%d" % (fam, i))))

    for lines in work:
        got = run_lk.run("\n".join(lines) + "\n")
        assert got == model.expect(lines), "the wrapped reference no longer agrees with the model"
    return {k: v for k, v in ROWS.items() if v}
