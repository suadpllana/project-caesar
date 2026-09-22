"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: the mode a resource
currently carries, how many children it has, how deep it is, the ages of the transactions in
the way, the threshold and what else is sitting on the resource. Nothing says whether a mode
was asked for or only derived, because the shipped hold table keeps one mode per transaction
and resource and building the distinction is the work; nothing says which level a claim was
refused at, for the same reason.

The verdict to want is that at least one graded quantity has no short rule. Two should be
short, and both are stated rules with nothing hidden behind them: whether a conflicting holder
gives way or refuses is the age comparison the brief states, and whether a claim is tried in a
sweep is whether its level moved. The two that should not be short are what mode a resource
comes to carry, which is a supremum over a quantity the shipped tree does not hold, and
whether giving a resource up leaves a claim, which turns on the same missing distinction.

    python3 tools/onelinecheck.py grant-widen-yield
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

RANK = {None: 0, "IS": 1, "IX": 2, "S": 3, "SIX": 4, "X": 5}

ROWS = {"cover-mode": [], "claim-left": [], "widen-fire": [], "give-or-refuse": []}


def _depth(res):
    return res.count(".")


def _watch(book_mod, give_mod, step_mod, wide_mod, ages_box):
    """Mirror four decision points of the reference, writing down what was visible."""
    raw_retune = book_mod.Book.retune
    raw_hand = give_mod.hand
    raw_take = step_mod.take
    raw_widen = wide_mod.widen

    def retune(self, t, res, out):
        before = self.eff(t, res)
        kids = self.kids(t, res)
        low = sum(1 for k in kids if self.eff(t, k) in ("IS", "S"))
        high = len(kids) - low
        raw_retune(self, t, res, out)
        ROWS["cover-mode"].append(({
            "was": RANK[before], "kids": len(kids), "low": low, "high": high,
            "depth": _depth(res),
        }, RANK[self.eff(t, res)]))

    def hand(book, due, u, res, out):
        seen = [(r, book.eff(u, r)) for r in book.sub(u, res)]
        before = set(due.held(u))
        raw_hand(book, due, u, res, out)
        after = set(due.held(u))
        for node, was in seen:
            ROWS["claim-left"].append(({
                "mode": RANK[was], "depth": _depth(node),
                "kids": sum(1 for r, _m in seen if r != node and r.startswith(node + ".")),
                "top": 1 if node == res else 0,
            }, 1 if (node in after and node not in before) else 0))

    def take(book, due, ages, t, res, m, out, loud):
        chain = step_mod.name.chain(res)
        want = step_mod.chain_want(book, t, res, m)
        watched = None
        for node in chain:
            goal = want[node]
            if book.eff(t, node) == goal or not book.clash(t, node, goal):
                continue
            foes = book.foes(t, node, goal)
            watched = ({
                "mine": ages[t], "oldest": min(ages[u] for u in foes),
                "foes": len(foes), "depth": _depth(node), "goal": RANK[goal],
            },)
            break
        got = raw_take(book, due, ages, t, res, m, out, loud)
        if watched is not None:
            ROWS["give-or-refuse"].append((watched[0], 0 if got else 1))
        return got

    def widen(book, due, ages, lim, out):
        # Never call wide_mod.pairs() here: it drains the work list the real rule reads,
        # which silently switched widening off and made this question one-sided.
        seen = []
        cands = set()
        for t in list(ages):
            for node in book.held(t):
                if book.kids(t, node):
                    cands.add((t, node))
        for t, node in sorted(cands):
            kids = book.kids(t, node)
            want = book.asked(t, node)
            for kid in kids:
                want = book_mod.mode.sup(want, book.eff(t, kid))
            others = [um for u, um in book.at(node).items() if u != t]
            seen.append(((t, node), {
                "kids": len(kids), "lim": lim, "others": len(others),
                "worst": max([RANK[x] for x in others] or [0]), "want": RANK[want],
            }, len(book.held(t))))
        raw_widen(book, due, ages, lim, out)
        for (t, node), row, before in seen:
            ROWS["widen-fire"].append((row, 1 if len(book.held(t)) < before else 0))

    book_mod.Book.retune = retune
    give_mod.hand = hand
    step_mod.take = take
    step_mod.keep.settle.__globals__  # keep the settle binding honest; no rebinding needed
    wide_mod.widen = widen


def samples():
    here = lab.tree(lab.SOL)
    run_lk = lab.inproc(here)
    from lk import give, hold, step, wide
    _watch(hold, give, step, wide, None)
    _cases, gen, _model = lab.sealed()
    small = [f for f, big in gen.FAMILIES if not big]
    for fam in small:
        for i in range(8):
            rng = random.Random("decisions|%s|%d" % (fam, i))
            run_lk.run("\n".join(gen.MAKE[fam](rng)) + "\n")
    return ROWS
