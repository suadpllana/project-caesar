"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment a read is about to be decided: the present
version, the allowance, the width of the range, the two fetch-shaping numbers, and what the
cache holds near the range read the way the *shipped* table holds it - a key range and the one
number a fetch came back with. Nothing here says which versions a cached range is correct for,
because the shipped table has no such field and building one is the work; nothing says which
of them are correct together, for the same reason.

The verdict to want is that at least one graded quantity has no short rule. The one that must
not is how far back the answer is served, because the version it lands on is a maximisation
over ranges that overlap in keys and differ in versions, and none of that is a field. Whether
a read fetches at all is the same question asked as a yes or no, so it should be no shorter.
The number of runs a fetch is split into may well be short - it is stated plainly, and
`cheat-slack-gap`, `cheat-cap-span` and `cheat-cap-at-cap` cover the readings that get it
wrong.

The watched copy below is asserted to reproduce the sealed model's trace on every program it
reports on, so a copy that drifted cannot quietly report on a different engine.

    python3 tools/onelinecheck.py stale-cover-serve
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"served-back": [], "fetched": [], "fetch-runs": []}


def _shipped_view(near, lo, hi, now, s):
    """What the shipped table would show: key ranges and the number a fetch came back with."""
    ents = [(st.lo, st.hi, st.born) for st in near if st.hi >= lo and st.lo <= hi]
    fresh = [e for e in ents if now - e[2] <= s]

    def holes(box):
        spans = sorted((max(a, lo), min(b, hi)) for a, b, _ in box)
        runs = []
        at = lo
        for a, b in spans:
            if a > at:
                runs.append((at, a - 1))
            if b + 1 > at:
                at = b + 1
            if at > hi:
                break
        if at <= hi:
            runs.append((at, hi))
        return runs

    return {
        "ents": len(ents),
        "fresh": len(fresh),
        "holes_all": len(holes(ents)),
        "holes_fresh": len(holes(fresh)),
        "cover_all": 0 if holes(ents) else 1,
        "cover_fresh": 0 if holes(fresh) else 1,
    }


def samples():
    here = lab.tree(lab.SOL)
    mod = lab.driver(here)
    ask = sys.modules["rng.ask"]
    hole = sys.modules["rng.hole"]
    mend = sys.modules["rng.mend"]
    knit = sys.modules["rng.knit"]
    pick = sys.modules["rng.pick"]
    out = sys.modules["rng.out"]

    def read(tb, st, lo, hi, s, tune):
        feat = _shipped_view(tb.near(lo, hi), lo, hi, st.ver, s)
        feat.update({"now": st.ver, "s": s, "width": hi - lo + 1,
                     "slack": tune.slack, "cap": tune.cap, "horizon": min(tune.horizon, 999)})
        lines = []
        at = pick.at(tb, lo, hi, s, st.ver)
        runs = 0
        if at is None:
            shaped = mend.shape(hole.runs(tb.near(lo, hi), lo, hi), lo, hi,
                                tune.slack, tune.cap)
            runs = len(shaped)
            for a, b in shaped:
                lines.append(out.fetch(a, b))
                rows, mark = st.at(a, b)
                tb.add(a, b, rows, mark)
            at = st.ver
        lines.append(out.ans(at, knit.rows(tb.near(lo, hi), lo, hi, at)))
        ROWS["served-back"].append((dict(feat), st.ver - at))
        ROWS["fetched"].append((dict(feat), runs > 0))
        if runs:
            ROWS["fetch-runs"].append((dict(feat), runs))
        return lines

    ask.read = read

    gen = lab.gen()
    cases = lab.cases()
    model = lab.model()
    work = [("hand", n, cases.prog(n)) for n in cases.ORDER]
    for fam in gen.SMALL:
        for i in range(6):
            rng = random.Random("decisions|%s|%d" % (fam, i))
            work.append((fam, "%s-%d" % (fam, i), gen.BUILD[fam](rng)))
    for fam, name, prog in work:
        text = "\n".join(prog) + "\n"
        got = mod.run(text)
        assert got == model.trace(text), "the watched copy drifted on %s" % name
    return ROWS
