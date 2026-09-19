"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: the arriving token's
weight at that expert, what the buffer holds and the weights of its occupants, the rank being
tried, the microbatch, the buffer size and the bank budget. Nothing says which occupants have
already been displaced this step, because the shipped service has no such field and building
one is part of the work; nothing says what a bank's load will be after an earlier bank cascades
into it, for the same reason.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
whether a full expert gives up an occupant, because the eligible occupant is not the weakest
one the buffer shows, and whether a bank sheds, because the load that decides it is not the
load the streaming pass left. The queue decision should be short - it is a stated rule with
nothing hidden behind it, and `cheat-defer-any-short` covers the reading that gets it wrong.

The watched copies below mirror the reference and are asserted to reproduce the sealed model's
trace on every program, so a copy that drifted cannot quietly report on a different engine.

    python3 tools/onelinecheck.py expert-defer-shed
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"displace": [], "queue": [], "shed-bank": [], "want-width": []}


def _install(here):
    sys.path.insert(0, str(here))
    for name in [n for n in sys.modules if n == "run_lay" or n == "lay" or n.startswith("lay.")]:
        del sys.modules[name]
    import run_lay
    from lay import gate, put, trim
    return run_lay, gate, put, trim


def _watch(gate, put, trim):
    """put._admit and trim.shed, mirrored with the decisions written down."""

    def admit(cfg, weights, order, bufs, st, token, last, out):
        before = len(st.wl[token]) if st.wl[token] else 0
        wl = gate.want(order[token], weights[token], cfg.w, st.blocked[token])
        if before:
            ROWS["want-width"].append(({
                "w0": before, "struck": len(st.blocked[token]), "ex": cfg.ex,
                "cap": bufs.c,
            }, len(wl)))
        st.wl[token] = wl
        held = []
        for e in wl:
            weight = weights[token][e]
            slot = bufs.free(e)
            if slot is None:
                seen = sorted(weights[t][e] for t in bufs.at(e).values())
                weak = bufs.weakest(e, st.gone)
                took = weak is not None and weak[0] < weight
                ROWS["displace"].append(({
                    "mine": weight,
                    "low": seen[0] if seen else 0,
                    "high": seen[-1] if seen else 0,
                    "span": (seen[-1] - seen[0]) if seen else 0,
                    "occ": len(seen),
                    "rank": len(held),
                    "cap": bufs.c,
                    "want": len(wl),
                }, took))
                if not took:
                    st.refuse(token, e)
                    break
                put._oust(bufs, st, weights, weak[2], e, last, out)
                bufs.seize(e, weak[1], token, weight)
                held.append((e, weak[1]))
                continue
            held.append((e, bufs.fill(e, token, weight)))
        st.place[token] = held
        ROWS["queue"].append(({
            "placed": len(held), "want": len(wl), "last": int(last),
            "cap": bufs.c, "ex": cfg.ex,
        }, bool(wl and not held and not last)))
        if wl and not held:
            st.defer(token, last, out)

    real_shed = trim.shed

    def shed(cfg, weights, bufs, st, z):
        before = {}
        for k in range(cfg.banks()):
            lo = k * cfg.bw
            before[k] = sum(bufs.count(e) for e in range(lo, lo + cfg.bw))
        held = {k: dict(bufs.at(e)) for k in range(cfg.banks())
                for e in range(k * cfg.bw, k * cfg.bw + cfg.bw)}
        real_shed(cfg, weights, bufs, st, z)
        for k in range(cfg.banks()):
            lo = k * cfg.bw
            after = sum(bufs.count(e) for e in range(lo, lo + cfg.bw))
            ROWS["shed-bank"].append(({
                "load": before[k], "z": z, "bank": k, "banks": cfg.banks(),
                "cap": bufs.c, "bw": cfg.bw,
            }, after < before[k]))
        assert held is not None

    put._admit = admit
    trim.shed = shed


def samples():
    here = lab.tree(lab.SOL)
    run_lay, gate, put, trim = _install(here)
    _watch(gate, put, trim)

    _cases, gen, model = lab.sealed()
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(10):
            rng = random.Random("decide|%s|%d" % (fam, i))
            lines = gen.build(fam, rng)
            got = run_lay.run("\n".join(lines) + "\n")
            assert got == model.expect(lines), \
                "the watched copy drifted from the contract on %s-%d" % (fam, i)
    return ROWS


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        kinds = len({str(y) for _r, y in rows})
        print("%-12s %d rows, %d outcomes" % (name, len(rows), kinds))
