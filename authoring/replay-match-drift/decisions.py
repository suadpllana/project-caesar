"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: the command's count within
its kind, how many commands of that kind the history recorded, how many answers carry that kind
or that name, how many recorded commands have been matched, how many are outstanding and how
many of those have an answer at all. Nothing says which side of the boundary the run is on
before the decision is made, because the shipped engine has no such flag for the run as a whole;
nothing says where an answer sits in the history, because that is what binding produces.

The verdict to want is that at least one graded quantity has no short rule. `replayed` should be
close to one - a command is replayed when its kind still has a record at its count - and it is
not quite, because the boundary is global and a later command of another kind is live with a
record still standing. The other four should not be short at all.

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

ROWS = {"replayed": [], "answer-pos": [], "race-pick": [], "mark-value": [], "leftover": []}


def _install(here):
    for key in [k for k in sys.modules if k == "dur" or k.startswith("dur.") or k == "run_dur"]:
        del sys.modules[key]
    sys.path.insert(0, str(here))
    import run_dur
    from dur import edge, pair, pend, ver
    return run_dur, edge, pair, pend, ver


def _watch(edge, pair, pend, ver):
    slot, bind = edge.Edge.slot, pair.Pair.bind
    fastest, pick, left = pend.Pend.fastest, ver.Ver.pick, edge.Edge.leftover

    def all_go(tab):
        return sum(len(v) for v in tab.go.values())

    def watched_slot(self, kind):
        at = self.n.get(kind, 0)
        mine = len(self.tab.go.get(kind, []))
        got = slot(self, kind)
        ROWS["replayed"].append(
            ([at, mine, all_go(self.tab), len(self.hit)], 0 if got[1] is None else 1))
        return got

    def watched_bind(self, tab_kind, name, idx, replayed):
        rec = bind(self, tab_kind, name, idx, replayed)
        same_pair = len(self.tab.ok.get((tab_kind, name), []))
        same_kind = sum(len(v) for k, v in self.tab.ok.items() if k[0] == tab_kind)
        every = sum(len(v) for v in self.tab.ok.values())
        label = -1 if rec.pos is None else (-2 if rec.pos >= 1 << 29 else rec.pos)
        ROWS["answer-pos"].append(
            ([idx, 1 if replayed else 0, same_pair, same_kind, every, self.at], label))
        return rec

    def watched_fastest(self):
        got = fastest(self)
        answered = sum(1 for rec in self.q if rec.pos is not None)
        ROWS["race-pick"].append(
            ([len(self.q), answered, 1 if self.q[0].pos is not None else 0,
              len(self.q) - 1], self.q.index(got)))
        return got

    def watched_pick(self, key, cur, live):
        held = len(self.tab.ch.get(key, []))
        seen = self.n.get(key, 0)
        got = pick(self, key, cur, live)
        ROWS["mark-value"].append(([cur, 1 if live else 0, held, seen], got))
        return got

    def watched_left(self):
        got = left(self)
        ROWS["leftover"].append(
            ([len(self.hit), len(self.tab.issued()), sum(self.n.values())],
             -1 if got is None else got[1]))
        return got

    edge.Edge.slot = watched_slot
    pair.Pair.bind = watched_bind
    pend.Pend.fastest = watched_fastest
    ver.Ver.pick = watched_pick
    edge.Edge.leftover = watched_left


def samples():
    cases, gen, model = lab.sealed()
    here = lab.tree(lab.SOL)
    run_dur, edge, pair, pend, ver = _install(here)
    _watch(edge, pair, pend, ver)
    work = [("hand", n, cases.prog(n)) for n in cases.ORDER]
    work += [(f, n, l) for f, n, l in gen.programs("decisions", 6)
             if f not in ("long", "wide")]
    for _fam, name, lines in work:
        got = run_dur.run("\n".join(lines) + "\n")
        assert got == model.expect(lines), "the watched reference drifted on %s" % name
    return {key: rows for key, rows in ROWS.items() if rows}
