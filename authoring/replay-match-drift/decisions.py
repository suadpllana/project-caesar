"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: how many branches can run,
how many are waiting, how many are set aside, how many exist, the command's count within its
kind, how many commands of that kind the history recorded, and how many answers carry that kind
or that name. Nothing says where an answer sits in the history, because that is what binding
produces, and nothing says which branch is next, because that is the thing the task is about.

The verdict to want is that at least one graded quantity has no short rule. `which-branch` is
the one that matters: the branch that runs next is decided by a position in the history that no
count of branches can stand in for.

The wrappers below sit on the reference itself rather than on a copy, and the run they produce
is asserted line for line against the sealed model, so a drifted watcher cannot report on a
different engine.

    python3 tools/onelinecheck.py replay-match-drift
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"replayed": [], "answer-pos": [], "which-branch": [], "wake-mark": [],
        "mark-value": [], "leftover": []}


def _install(here):
    for key in [k for k in sys.modules if k == "dur" or k.startswith("dur.") or k == "run_dur"]:
        del sys.modules[key]
    sys.path.insert(0, str(here))
    import run_dur
    from dur import edge, pair, sched, ver, wake
    return run_dur, edge, pair, sched, ver, wake


def _watch(edge, pair, sched, ver, wake):
    slot, bind = edge.Edge.slot, pair.Pair.bind
    pick, park = sched.Sched.pick, sched.Sched.park
    mark, choose, left = wake.Wake.mark, ver.Ver.pick, edge.Edge.leftover

    def all_go(tab):
        return sum(len(v) for v in tab.go.values())

    def watched_slot(self, kind):
        at = self.n.get(kind, 0)
        mine = len(self.tab.go.get(kind, []))
        got = slot(self, kind)
        ROWS["replayed"].append(
            ({"count": at, "of_kind": mine, "recorded": all_go(self.tab),
              "matched": len(self.hit)}, 0 if got[1] is None else 1))
        return got

    def watched_bind(self, kind, name, idx, replayed):
        rec = bind(self, kind, name, idx, replayed)
        same_pair = len(self.tab.ok.get((kind, name), []))
        same_kind = sum(len(v) for k, v in self.tab.ok.items() if k[0] == kind)
        every = sum(len(v) for v in self.tab.ok.values())
        label = -1 if rec.pos is None else rec.pos
        ROWS["answer-pos"].append(
            ({"count": idx, "matched": 1 if replayed else 0, "of_pair": same_pair,
              "of_kind": same_kind, "answers": every, "taken": self.at}, label))
        return rec

    def watched_pick(self):
        free = len(self.ready)
        held = len(self.marked)
        dark = len(self.idle)
        got = pick(self)
        ROWS["which-branch"].append(
            ({"able": free, "waiting": held, "aside": dark, "branches": len(self.all)},
             -1 if got is None else got.bid))
        return got

    def watched_park(self, who, at):
        ROWS["wake-mark"].append(
            ({"branch": who.bid, "waiting": len(self.marked), "aside": len(self.idle),
              "branches": len(self.all)}, -1 if at is None else at))
        return park(self, who, at)

    def watched_choose(self, key, cur, live):
        held = len(self.tab.ch.get(key, []))
        seen = self.n.get(key, 0)
        got = choose(self, key, cur, live)
        ROWS["mark-value"].append(
            ({"asked": cur, "live": 1 if live else 0, "held": held, "seen": seen}, got))
        return got

    def watched_left(self):
        got = left(self)
        ROWS["leftover"].append(
            ({"matched": len(self.hit), "recorded": len(self.tab.issued()),
              "issued": sum(self.n.values())}, -1 if got is None else got[1]))
        return got

    edge.Edge.slot = watched_slot
    pair.Pair.bind = watched_bind
    sched.Sched.pick = watched_pick
    sched.Sched.park = watched_park
    ver.Ver.pick = watched_choose
    edge.Edge.leftover = watched_left


def samples():
    cases, gen, model = lab.sealed()
    here = lab.tree(lab.SOL)
    run_dur, edge, pair, sched, ver, wake = _install(here)
    _watch(edge, pair, sched, ver, wake)
    work = [("hand", n, cases.prog(n)) for n in cases.ORDER]
    work += [(f, n, l) for f, n, l in gen.programs("decisions", 6)
             if f not in ("long", "wide")]
    for _fam, name, lines in work:
        got = run_dur.run("\n".join(lines) + "\n")
        assert got == model.expect(lines), "the watched reference drifted on %s" % name
    return {key: rows for key, rows in ROWS.items() if rows}
