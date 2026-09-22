"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: for a stretch, how many
entries of the key it holds and of which kinds, where its floor and top sit and where the head
is; for a trailing point, the head, how many feeds are live, how many of them reach this key,
and the lowest position among all of them; for a collapse, what the pair stands to remove,
where its span top is, which key it belongs to, the budget, and how many pairs were standing
when the command began. Nothing says what a key is worth at a boundary, because working that
out is the task, and nothing says where a pair sits in the order, because that is the answer.

The verdict to want is that at least one graded quantity has no short rule. Two should be
short: the trailing point, which is a stated rule with nothing hidden behind it and is covered
by `cheat-trailing-any-feed` and `cheat-trailing-highest`, and whether a pair is collapsed
under the budget. Whether a stretch keeps an entry should not be, because the same counts of
`set`, `add` and `del` entries keep an entry or lose it depending on what the key was worth
below the stretch - which is the thing a solver has to derive rather than read.

The watched copy below is the reference, and it is asserted to reproduce the sealed model's
trace on every program it walks, so a copy that had drifted could not quietly report on a
different engine.

    python3 tools/onelinecheck.py feed-lag-pare
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"span-keeps": [], "trailing": [], "pare-takes": []}
CAP = 6000


def _install():
    here = lab.tree(lab.SOL)
    sys.path.insert(0, str(here))
    for name in [n for n in sys.modules if n in ("run_log", "lg") or n.startswith("lg.")]:
        del sys.modules[name]
    import run_log
    from lg import fold, pare, pin, span
    return run_log, fold, pare, pin, span


def _watch(fold, pare, pin, span):
    """pin.trailing, span.build and pare.run, mirrored with the decisions written down."""
    was_trailing = pin.Pins.trailing
    was_build = span.build
    was_collapse = span.collapse
    was_run = pare.run
    taken = set()

    def trailing(self, key):
        got = was_trailing(self, key)
        if len(ROWS["trailing"]) < CAP:
            reach = sum(1 for _p, lo, hi in self.fd.values() if lo <= key <= hi)
            low = min((p for p, _lo, _hi in self.fd.values()), default=self.st.head)
            ROWS["trailing"].append(({"head": self.st.head, "feeds": len(self.fd),
                                      "reach": reach, "low": low,
                                      "marks": len(self.mk)}, got))
        return got

    def build(store, pins, key):
        rows = was_build(store, pins, key)
        if len(ROWS["span-keeps"]) < CAP:
            for floor, edge, count, _last, lo, hi in rows:
                kinds = [store.entry(s)[0] for s in store.at(key, floor, edge)]
                ROWS["span-keeps"].append(({
                    "count": count,
                    "sets": kinds.count("set"),
                    "adds": kinds.count("add"),
                    "dels": kinds.count("del"),
                    "floor": floor,
                    "edge": edge,
                    "head": store.head,
                }, not fold.same(lo, hi)))
        return rows

    def collapse(store, key, floor, edge, last, lo, hi):
        taken.add((key, floor))
        return was_collapse(store, key, floor, edge, last, lo, hi)

    def run(store, pins, budget):
        standing = []
        for key in list(store.idx):
            for floor, edge, count, _last, lo, hi in was_build(store, pins, key):
                won = count - (0 if fold.same(lo, hi) else 1)
                if won > 0:
                    standing.append((won, edge, key, floor))
        taken.clear()
        live = store.count()
        got = was_run(store, pins, budget)
        if len(ROWS["pare-takes"]) < CAP:
            most = max((w for w, _e, _k, _f in standing), default=0)
            for won, edge, key, floor in standing:
                ROWS["pare-takes"].append(({"won": won, "edge": edge, "key": key,
                                            "budget": budget, "live": live,
                                            "pairs": len(standing), "most": most},
                                           (key, floor) in taken))
        return got

    pin.Pins.trailing = trailing
    span.build = build
    span.collapse = collapse
    pare.run = run


def samples():
    run_log, fold, pare, pin, span = _install()
    _watch(fold, pare, pin, span)
    _cases, gen, model = lab.sealed()
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(12):
            lines = gen.MAKERS[fam](random.Random("decide|%s|%d" % (fam, i)))
            got = run_log.run("\n".join(lines) + "\n")
            assert got == model.expect(lines), "the watched copy has drifted: %s-%d" % (fam, i)
    return ROWS
