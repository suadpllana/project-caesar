"""The reference against the sealed model, and both against a definitional search.

Three things are checked and each one is cheap:

  * the reference and tests/oracle.py agree on every row of every random stream;
  * on small rounds the settlement the reference reaches is the one an exhaustive search
    over every depth vector calls the largest that stands up, which is what says the
    two are computing the requirement rather than the same mistake;
  * the exhaustive search never finds two largest answers, which is what makes the
    requirement well posed and keeps a correct alternative from being failed for a
    choice the rules never made.
"""
import itertools
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tests"))

import harness
import oracle
import gen


def _search(hold, lines, obs, reach):
    who = sorted(lines)
    best = None
    for d in itertools.product(*[range(reach[n] + 1) for n in who]):
        got = {n: 0 for n in who}
        pay = {n: 0 for n in who}
        for j, n in enumerate(who):
            for i in lines[n][: d[j]]:
                pay[n] += obs[i][2]
                got[obs[i][1]] += obs[i][2]
        if all(hold[n] + got[n] - pay[n] >= 0 for n in who):
            v = dict(zip(who, d))
            best = v if best is None else {n: max(best[n], v[n]) for n in who}
    got = {n: 0 for n in who}
    pay = {n: 0 for n in who}
    for n in who:
        for i in lines[n][: best[n]]:
            pay[n] += obs[i][2]
            got[obs[i][1]] += obs[i][2]
    assert all(hold[n] + got[n] - pay[n] >= 0 for n in who), "two answers, neither on top"
    return best


def small(rounds, seed=5):
    r = random.Random(seed)
    for _ in range(rounds):
        who = ["a", "b", "c", "d"][: r.randint(2, 4)]
        hold = {n: r.choice([0, 0, 0, 1, 3, 6]) for n in who}
        obs = {}
        lines = {n: [] for n in who}
        k = 0
        for n in who:
            for _ in range(r.randint(0, 3)):
                pe = r.choice([x for x in who if x != n])
                i = "o%d" % k
                k += 1
                obs[i] = (n, pe, r.randint(1, 9), 1)
                lines[n].append(i)
        reach = {n: len(lines[n]) for n in who}
        want = _search(hold, lines, obs, reach)
        got = oracle._settle(dict(hold), {n: list(v) for n, v in lines.items()}, obs, reach)
        assert got == want, "the model missed the largest answer: %s vs %s" % (got, want)
    return rounds


def streams(n, seed="a17c0ffee"):
    bad = 0
    for tag, text in gen.batch(seed, n):
        if harness.run(str(ROOT / "solution"), text) != _shape(oracle.play(text)):
            bad += 1
    return bad


def _shape(r):
    return {"log": [tuple(x) for x in r["log"]], "sheet": r["sheet"]}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    print("definitional search on %d small rounds: ok" % small(600))
    bad = streams(n)
    print("reference against the sealed model on %d streams: %d disagreements" % (n, bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
