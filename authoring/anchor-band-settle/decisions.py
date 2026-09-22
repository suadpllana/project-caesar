#!/usr/bin/env python3
"""The graded decisions as rows of features the agent can actually read. Never ships.

`tools/onelinecheck.py` searches for the shortest exact rule over these features - field
against field or against a small constant, at depth one or two. The features offered are the raw
ones the tree exposes at frame time: whether the pre-frame holder is gone, laid out, of zero
height or stuck at the offset the settle starts from, how long its chain is, whether the band is
non-zero there, and whether the frame carried an explicit scroll or a live edit. Nothing derived
is offered - the band-relative distance, the per-pass offsets, the settled result - because the
derivation is the task.

The verdict to want is that at least one graded quantity has no short rule. `settle_offset` is a
fixed point over up to four passes and equals no single feature. `fell_back` - whether a
container took the view over because the holder was disqualified partway through the settle -
is not the depth-two test `holder gone or holder stuck at the old offset`, because a holder can
qualify on the first pass, move the offset, and only then be stuck. `switched_off`, by contrast,
is exactly `an explicit scroll or a live edit`, and the tool should find that rule, which is the
control that says the search works.

    python3 authoring/anchor-band-settle/decisions.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import lab  # noqa: E402


def _frames(lines):
    decls, frames = [], []
    for raw in lines:
        p = raw.split()
        if not p:
            continue
        if p[0] == "frame":
            frames.append([])
        elif p[0] in ("view", "box", "at"):
            decls.append(raw)
        else:
            frames[-1].append(p)
    return decls, frames


def samples():
    _cases, gen, model = lab.sealed()
    offset_rows, fell_rows, switch_rows = [], [], []

    for _fam, _name, lines in gen.programs("decisions", 10, small_only=True):
        decls, frames = _frames(lines)
        world, s = model.begin(decls)
        root = world.root
        for edits in frames:
            band0 = world.band(s)
            held = world.pick(s, band0)
            chain = []
            x = held
            while x is not None and x is not root:
                chain.append(x)
                x = x.up
            chain_ids = [b.id for b in chain]
            s_old = s

            s2, word = model.one_frame(world, s, edits)

            is_scroll = int(any(e[0] == "to" for e in edits))
            # control: an explicit scroll always prints off scroll and nothing else does, so the
            # tool must find `is_scroll` here - the negative results below mean something only if
            # the search can find a rule when one exists.
            switch_rows.append((
                {"is_scroll": is_scroll, "picked": int(held is not None),
                 "chain_len": len(chain_ids)},
                bool(word == "off scroll")))

            # holder-role decisions only where a real holder was picked and nothing switched
            if held is not None and word not in ("off scroll", "off live", "none"):
                h0 = chain[0]
                gone = h0.id not in world.by
                row = {
                    "h0_gone": int(gone),
                    "h0_shows": int((not gone) and world.shows(h0)),
                    "h0_zero": int((not gone) and h0.h <= 0),
                    "h0_stuck_old": int((not gone) and world.under_stuck(h0, s_old)),
                    "chain_len": len(chain_ids),
                    "has_parent": int(len(chain_ids) > 1),
                    "band_pos": int(band0 > 0),
                }
                fell_rows.append((row, bool(word in chain_ids[1:])))

            if word not in ("off scroll", "off live", "none"):
                # the settled offset against every raw offset-like number in view
                offset_rows.append((
                    {"old_offset": s_old, "band_old": band0,
                     "span": world.span(), "vh": world.vh}, s2))

            s = s2

    return {"settle_offset": offset_rows, "fell_back": fell_rows, "scrolled_off": switch_rows}


if __name__ == "__main__":
    got = samples()
    for k, v in sorted(got.items()):
        print("%-14s %5d rows, %d distinct labels" % (k, len(v), len({y for _, y in v})))
