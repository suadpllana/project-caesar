"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: whether a predicate holds
now, how many goals a goal stands on, how many of those are in the credited set the shipped
book keeps, how deep into the episode the step is, what the budget has spent and how long the
step is. Nothing says at which observation a prerequisite was credited, because the shipped book
is a plain set with no such field and building one is part of the work; nothing says what the
records will look like after a step is rolled back, for the same reason.

The verdict to want is that at least one graded quantity has no short rule. Measured on
2026-09-22, none of the four has one. The two that were expected to resist are whether a goal is
credited at this observation, because the set the shipped book keeps cannot say whether a
prerequisite landed strictly earlier, and whether a step is the one that closes the episode,
because the shipped budget check compares the wrong pair. The other two were expected to be
short and are not, which is a weaker claim than it sounds: `cheat-rearm-now` and
`cheat-void-cone-shut` are what actually cover the readings that get them wrong.

The watched copy below mirrors the reference and is asserted to reproduce the sealed model's
trace on every trail, so a copy that drifted could not quietly report on a different engine.

    python3 tools/onelinecheck.py trail-credit-void
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"credit": [], "rearm": [], "cone-shut": [], "step-cut": []}


def _install(here):
    sys.path.insert(0, str(here))
    for name in [n for n in list(sys.modules)
                 if n == "run_crd" or n == "crd" or n.startswith("crd.")]:
        del sys.modules[name]
    import run_crd
    from crd import book as bk
    from crd import ep, pred, void
    return run_crd, bk, ep, pred, void


def _watch(bk, ep, pred, void):
    """Book.credit, void.fire and ep.run, mirrored with the decisions written down."""
    real_credit = bk.Book.credit
    real_fire = void.fire

    def credit(self, store, moved, delta):
        held = sum(1 for g in range(len(self.goals)) if self.state[g] == bk.HELD)
        for gid in sorted(set(self.queue) | {g for key in moved
                                             for g in self.at_key.get(key, ())}):
            one = self.goals[gid]
            if self.state[gid] == bk.HELD:
                continue
            got = 1 if pred.holds(one, store) else 0
            up_held = sum(1 for p in one.pre if self.state[p] == bk.HELD)
            row = {"holds": got, "pre": len(one.pre), "pre_held": up_held,
                   "held": held, "goals": len(self.goals), "gid": gid}
            if self.state[gid] == bk.SHUT:
                ROWS["rearm"].append((dict(row), 0 if got else 1))
            else:
                ROWS["credit"].append((row, 1 if (got and self.ready[gid] == 0) else 0))
        return real_credit(self, store, moved, delta)

    def fire(book, bar, delta):
        for gid in void.cone(book, bar.goal):
            ROWS["cone-shut"].append((
                {"gid": gid, "named": bar.goal, "held": 1 if book.state[gid] == bk.HELD else 0,
                 "pre": len(book.goals[gid].pre), "dep": len(book.dep[gid])},
                1 if gid == bar.goal else 0))
        return real_fire(book, bar, delta)

    real_run = ep.run

    def run(cfg, one, store, sums, out):
        spent = 0
        for actions, good in one.steps:
            room = cfg.budget - spent
            take = min(len(actions), max(room, 0))
            ROWS["step-cut"].append((
                {"used": spent, "budget": cfg.budget, "acts": len(actions),
                 "ok": 1 if good else 0, "steps": len(one.steps)},
                1 if take != len(actions) else 0))
            spent += take
            if take != len(actions):
                break
        return real_run(cfg, one, store, sums, out)

    bk.Book.credit = credit
    void.fire = fire
    ep.run = run


def samples():
    for key in ROWS:
        ROWS[key] = []
    here = lab.tree(lab.SOL)
    run_crd, bk, ep, pred, void = _install(here)
    _watch(bk, ep, pred, void)
    _cases, gen, model = lab.sealed()

    small = [f for f, big in gen.FAMILIES if not big]
    bad = []
    for fam in small:
        for turn in range(6):
            rnd = random.Random("decisions|%s|%d" % (fam, turn))
            lines = gen.MAKERS[fam](rnd)
            got = run_crd.run("\n".join(lines) + "\n")
            if got != model.expect(lines):
                bad.append("%s-%d" % (fam, turn))
    if bad:
        raise SystemExit("the watched copy has drifted from the model: %s" % bad[:3])
    return {key: rows for key, rows in ROWS.items() if rows}


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        yes = sum(1 for _f, label in rows if label)
        print("%-10s %5d rows, %d positive" % (name, len(rows), yes))
