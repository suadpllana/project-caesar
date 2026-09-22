"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment a decision is made: the row score, the tokens,
the beam's place and length, the step, how many members the kept set holds, and the four
settings that bear on it. Nothing says whether the span a candidate would add has been seen
before, because the shipped tree has no such field and building one is the work; nothing says
what the kept set is lending, for the same reason.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
whether a candidate is refused, because that depends on a history no shipped field carries,
and whether the search stops on its reach, because the comparison is an arithmetic one over
four settings rather than a comparison between two fields. Closing and overflowing should be
short - each is a stated rule with nothing behind it, and `stop-floor` and `pool-first` cover
the readings that get them wrong.

The watched copy below mirrors the reference and is asserted to reproduce the sealed model's
trace on every program it reports from, so a copy that had drifted could not quietly report on
a different stage.

    python3 tools/onelinecheck.py beam-ban-carry
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import model  # noqa: E402

ROWS = {"refuse": [], "close": [], "evict": [], "reach": []}


def _install():
    here = lab.tree(lab.TASK / "solution")
    for name in [n for n in list(sys.modules) if n == "run_beam" or n.startswith("bm")]:
        del sys.modules[name]
    sys.path.insert(0, str(here))
    import run_beam
    from bm import halt, keep, pick, rep, sc, say
    return run_beam, (halt, keep, pick, rep, sc, say)


def _watched(halt, keep, pick, rep, sc, say):
    """A copy of the reference step loop with every graded decision written down."""

    def one(sp, name, prompt):
        out = [say.ask(name)]
        tab = sc.Table(sp.rows)
        book = rep.Book(sp.n)
        lent = rep.Lent()
        pool = keep.Pool(sp.h)
        g = tab.top()
        beams = [(0, rep.root(book, prompt))]
        step = 0
        while True:
            step += 1
            moved = False
            for raw, path in beams:
                add = tab.stop(path.last)
                ROWS["close"].append(({
                    "ln": path.length, "s": sp.s, "stop": 0 if add is None else 1,
                    "step": step, "w": sp.w, "h": sp.h,
                }, bool(path.length >= sp.s and add is not None)))
                if path.length < sp.s or add is None:
                    continue
                ln = path.length
                fin = raw + add - sp.p * ln
                held = len(pool.mem)
                _new, went = pool.put(fin, ln, path)
                ROWS["evict"].append(({
                    "held": held, "h": sp.h, "ln": ln, "step": step,
                }, bool(went)))
                out.append(say.shut(step, ln, fin))
                moved = True
                for old in went:
                    out.append(say.gone(step, old.ln, old.fin))
            if moved:
                lent.reset(pool.masks())
            cands = []
            for slot, (raw, path) in enumerate(beams):
                rows = tab.out(path.last)
                for tok, add in rows:
                    bit = rep.reach(book, path, tok)
                    no = bool(bit >= 0 and (path.holds(bit) or lent.has(bit)))
                    ROWS["refuse"].append(({
                        "add": add, "tok": tok, "last": path.last, "slot": slot,
                        "ln": path.length, "step": step, "held": len(pool.mem),
                        "n": sp.n, "deg": len(rows), "top": g,
                    }, no))
                    if no:
                        continue
                    cands.append((raw + add, slot, tok, path))
            took = pick.take(cands, sp.w)
            best = max((cand[0] for cand in took), default=0)
            reason = halt.why(step, sp.t, took, pool, best, sp.p, g)
            if took and step < sp.t:
                low = pool.worst()
                ROWS["reach"].append(({
                    "step": step, "cap": sp.t, "left": sp.t - step, "held": len(pool.mem),
                    "h": sp.h, "best": best, "low": 0 if low is None else low,
                    "pen": sp.p, "top": g,
                }, reason == "bound"))
            if reason is not None:
                out.append(say.halt(step, reason))
                break
            beams = [(cand[0], rep.grow(book, cand[3], cand[2])) for cand in took]
        for rank, one_hyp in enumerate(pool.listing()):
            out.append(say.hyp(rank, one_hyp.fin, one_hyp.ln, one_hyp.path.tokens()))
        return out

    return one


def samples():
    run_beam, mods = _install()
    run_beam.walk.one = _watched(*mods)
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(14):
            lines = gen.make(fam, random.Random("decide|%s|%d" % (fam, i)))
            got = run_beam.run("\n".join(lines) + "\n")
            if got != model.expect(lines):
                raise SystemExit("the watched copy has drifted from the model on %s-%d" % (fam, i))
    return {name: rows for name, rows in ROWS.items() if rows}


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        yes = sum(1 for _r, label in rows if label)
        print("%-8s %5d rows, %d positive" % (name, len(rows), yes))
