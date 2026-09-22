"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: the offset, the viewport
height, the overscan, the pinned header's height, the room left to the next header, the total,
the foot, the first and last visible items, the flow length, and what the frame has measured so
far. Nothing says where the anchor line is, what the held item's top is or what the gap is,
because the shipped pane has no such quantity and building them is part of the work.

The verdict to want is that at least one graded quantity has no short rule. The settle-stop
decision should be short - it is a stated rule over two numbers the pass already has, and
`cheat-pass-offset-only` and `cheat-pass-meas-only` cover the readings that get it wrong. The
offset a pass settles at, the item it holds and where that hold lands after an edit should not
be, because each is a value computed from a geometry the shipped tree does not expose.

The instrumented driver below mirrors the reference and is asserted to reproduce the sealed
model's trace on every sampled document, so a copy that drifted could not quietly report on a
different pane.

    python3 tools/onelinecheck.py row-anchor-pass
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"band": [], "hold": [], "offset": [], "stop": [], "carry": []}


def _install():
    here = lab.tree(lab.SOL)
    sys.path.insert(0, str(here))
    for name in [n for n in list(sys.modules)
                 if n in ("run_pane", "pane") or n.startswith("pane.")]:
        del sys.modules[name]
    import run_pane  # noqa: F401
    from pane import band, geom, hold, move, say, spec, src, win
    return spec, src, say, geom, band, win, hold, move


def _play(mods, text):
    """The reference's own frame order, with every graded decision written down."""
    spec, src, say, geom, band, win, hold, move = mods
    cfg, decls, evs = spec.parse(text)
    doc = src.Doc(decls)
    gm = geom.Geom(doc)
    out = say.Out()

    class St:
        pass

    st = St()
    st.off = 0
    st.vh = cfg.vh
    st.foot = False

    for n, ev in enumerate(evs):
        move.apply(gm, st, ev)

        gi, b = band.band(gm, st.off)
        nxt = gm.gtop(gi + 1) if gi + 1 < gm.ngroups() else gm.total()
        ROWS["band"].append(({
            "hh": gm.ghh(gi), "room": nxt - st.off, "off": st.off, "vh": st.vh,
            "groups": gm.ngroups(), "total": gm.total(),
        }, b))

        first = gm.at(st.off)
        last = gm.at(st.off + st.vh - 1)
        held = hold.take(gm, st.off + b)
        ROWS["hold"].append(({
            "first": first, "last": last, "band": b, "off": st.off, "vh": st.vh,
            "count": gm.count(), "top_first": gm.top(first),
        }, held[0]))

        if ev[0] in ("ins", "del"):
            before = held[0]
            held = hold.track(gm, held, ev)
            ROWS["carry"].append(({
                "was": before, "at": ev[2], "n": ev[3],
                "kind": 1 if ev[0] == "ins" else 0, "count": gm.count(),
            }, held[0]))

        m = 0
        p = 0
        shown = (0, 0, 0, 0)
        while p < cfg.pcap:
            p += 1
            gi, b = band.band(gm, st.off)
            w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)
            shown = (gi, b, w0, w1)
            got = win.sweep(gm, w0, w1)
            m += got
            if st.foot:
                want = move.foot(gm.total(), st.vh)
            else:
                want = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)
            ROWS["offset"].append(({
                "off": st.off, "band": b, "w0": w0, "w1": w1, "got": got,
                "foot": move.foot(gm.total(), st.vh), "vh": st.vh, "total": gm.total(),
            }, want))
            ROWS["stop"].append(({
                "got": got, "moved": abs(want - st.off), "pass": p, "cap": cfg.pcap,
            }, bool(got == 0 and want == st.off)))
            if got == 0 and want == st.off:
                break
            st.off = want
        out.frame(n, st.off, gm.ggid(shown[0]), shown[1], shown[2], shown[3],
                  held[1], held[2], m, p)
    out.end(st.off, gm.total(), doc.meas)
    return out.lines


def samples():
    mods = _install()
    cases, gen, model = lab.sealed()
    for name in cases.ORDER:
        lines = cases.prog(name)
        assert _play(mods, "\n".join(lines) + "\n") == model.expect(lines), name
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(6):
            rng = random.Random("decide|%s|%d" % (fam, i))
            lines = gen.MAKERS[fam](rng)
            assert _play(mods, "\n".join(lines) + "\n") == model.expect(lines), (fam, i)
    return ROWS
