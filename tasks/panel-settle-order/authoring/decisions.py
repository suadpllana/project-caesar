"""The graded decisions as rows of features an agent can read at the moment it decides.

tools/onelinecheck.py searches these for the shortest exact rule over the fields the
environment already exposes. A graded decision a two-term rule reproduces is an easiness
rejection waiting to happen, because a frontier model writes two correct terms cold
whatever is hidden from it.

Three decisions are exported, one per question the engine has to answer:

  runs    for each gauge in each round, whether the round runs it at all
  order   for each gauge the round runs, its position in the run order
  trips   for each latch in each round, whether it trips

The features are what a submission can read off the panel and the round without doing any
of the work: where the entry is declared, how many entries its expression mentions and how
many of those are gauges, whether the expression is conditional, how big the panel is,
which round this is, and whether a feed the expression mentions was written this round.

How far a gauge stands from the feeds is NOT a feature, and neither is what it currently
reads. Working those out is the task, and handing them to the search would be asking
whether the answer predicts itself.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import oracle  # noqa: E402


def _mentions(node, out):
    if node[0] == "r":
        out.add(node[1])
        return
    if node[0] == "n":
        return
    for kid in node[1]:
        _mentions(kid, out)


def _shape(text):
    """Everything about a panel a submission can see before it runs anything."""
    feeds, code, lat, turns, order = oracle.read(text)
    ment = {}
    cond = {}
    for line in text.splitlines():
        bits = line.split()
        if not bits or bits[0] != "G":
            continue
        body = " ".join(bits[2:])
        node = oracle._build(oracle._split(body), 0)[0]
        names = set()
        # _build compiles to closures, so read the mentions off the text instead.
        for tok in oracle._split(body):
            if tok in ("add", "sub", "gt", "eq", "pick", "(", ")"):
                continue
            try:
                int(tok)
            except ValueError:
                names.add(tok)
        ment[bits[1]] = names
        cond[bits[1]] = 1 if "pick" in body else 0
    return feeds, lat, turns, order, ment, cond


def samples():
    out = {"runs": [], "order": [], "trips": []}
    panels = [(k, cases.PANELS[k]) for k in sorted(cases.PANELS)] + gen.build("decisions", 90)
    for _name, text in panels:
        got = oracle.check(text)
        if got is None:
            continue
        feeds, lat, turns, order, ment, cond = _shape(text)
        ix = {}
        for i, n in enumerate(order):
            ix[n] = i
        gauges = [n for n in order if n not in feeds]
        rounds = {}
        for rno, tag, name, _v in got["log"]:
            rounds.setdefault(rno, {"in": [], "cp": [], "tr": []})[tag].append(name)
        for rno in sorted(rounds):
            fired = rounds[rno]["in"]
            ran = rounds[rno]["cp"]
            for g in gauges:
                feat = {
                    "ix": ix[g],
                    "ment": len(ment.get(g, ())),
                    "mentg": sum(1 for m in ment.get(g, ()) if m not in feeds),
                    "cond": cond.get(g, 0),
                    "nf": len(feeds),
                    "ng": len(gauges),
                    "rno": rno,
                    "hitfeed": int(any(m in fired for m in ment.get(g, ()))),
                    "nfired": len(fired),
                }
                out["runs"].append((feat, int(g in ran)))
                if g in ran:
                    seat = dict(feat)
                    out["order"].append((seat, ran.index(g)))
            for nm, tgt, _wr in lat:
                feat = {
                    "ix": ix.get(tgt, 0),
                    "ment": len(ment.get(tgt, ())),
                    "mentg": sum(1 for m in ment.get(tgt, ()) if m not in feeds),
                    "cond": cond.get(tgt, 0),
                    "nf": len(feeds),
                    "ng": len(gauges),
                    "rno": rno,
                    "hitfeed": int(any(m in fired for m in ment.get(tgt, ()))),
                    "nfired": len(fired),
                }
                out["trips"].append((feat, int(nm in rounds[rno]["tr"])))
    return out


if __name__ == "__main__":
    s = samples()
    for k in sorted(s):
        labels = sorted(set(v for _f, v in s[k]))
        print("%-6s %5d samples, %d distinct labels" % (k, len(s[k]), len(labels)))
