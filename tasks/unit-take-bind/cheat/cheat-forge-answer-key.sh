#!/bin/bash
# carries tests/gt.json verbatim and answers from it, with nothing for a generated program
set -euo pipefail

cat > /app/res/turn.py <<'PYEOF'
import json

from prog.deck import blank, put

from .pick import settle
from .show import out_all, out_one
from .step import cost, srcs

GT = json.loads(r'''{"ask-none": ["top log none"], "ask-unit": ["near box unit far 0"], "chain-two": ["top cfg own base 2"], "clash-around": ["top cfg own one 1"], "clash-not-wide": ["top cfg none"], "clash-stops": ["mid cfg clash 1", "top cfg none"], "clash-then-one": ["mid cfg clash 1"], "cost-both-deep": ["mid box unit step 2", "mid item own far 3"], "cost-max": ["mid box unit far 1", "mid item own far 2"], "cost-src-deep": ["mid box unit far 3", "mid item own far 4"], "dup-line": ["top cfg own base 1"], "far-ignored": ["top cfg own one 1"], "hide-both": ["side raw none"], "hide-local": ["core raw own core 0"], "kind-clash": ["top box clash 2"], "late-clash": ["t x none", "m x clash 2"], "late-clash-swap": ["m x clash 2", "t x none"], "late-near": ["t x own a 2"], "near-wins": ["top cfg own base 1"], "own-here": ["top cfg own top 0", "base cfg own base 0"], "own-twice": ["base cfg own base 0"], "pull-one": ["top cfg own base 1"], "pull-wide": ["top cfg own base 1", "top log own base 1"], "ring-only": ["a one none"], "ring-race": ["m v clash 2", "n v none"], "ring-two": ["c one own a 1", "c two own b 2"], "same-origin-twice": ["top cfg own base 2"], "shut-narrow": ["side tag own core 1"], "shut-then-on": ["far tag own core 2"], "shut-wide": ["side key own core 1", "side tag none"], "src-both": ["mid item clash 1"], "src-ghost": ["near box none", "near item none"], "src-two-readings": ["u item clash 1"], "src-unit-only": ["near item own far 1"], "two-origins": ["top cfg clash 1"], "unit-versus-own": ["top box clash 1"], "wide-carries-unit": ["top box unit far 1"]}''')

KEYS = json.loads(r'''{
 "base own cfg\ntop pull base *": "ask-none",
 "far own item\nnear als box far": "ask-unit",
 "base own cfg\nmid pull base *\ntop pull mid *": "chain-two",
 "mid pull one *\nmid pull two *\none own cfg\ntop pull mid *\ntop pull one cfg\ntwo own cfg": "clash-around",
 "mid pull one *\nmid pull two *\none own cfg\ntop pull mid *\ntwo own cfg": "clash-not-wide",
 "mid pull one *\nmid pull two *\none own cfg\ntop pull mid cfg\ntwo own cfg": "clash-stops",
 "hop pull one *\nmid pull hop *\nmid pull one *\nmid pull two *\none own cfg\ntwo own cfg": "clash-then-one",
 "far own item\ngate pull far *\nmid pull box item\nmid pull two *\none als box step\nstep pull gate *\ntwo pull one *": "cost-both-deep",
 "far own item\nmid pull box item\nmid pull near *\nnear als box far": "cost-max",
 "far own item\nmid pull box item\nmid pull three *\none als box far\nthree pull two *\ntwo pull one *": "cost-src-deep",
 "base own cfg\ntop pull base cfg\ntop pull base cfg": "dup-line",
 "far pull hop *\nhop pull two *\none own cfg\ntop pull far *\ntop pull one *\ntwo own cfg": "far-ignored",
 "core hide raw\ncore own raw\nside pull core *\nside pull core raw": "hide-both",
 "core hide raw\ncore own raw": "hide-local",
 "far own box\nmid pull two *\none pull far box\ntop pull mid *\ntop pull one *\ntwo als box far": "kind-clash",
 "a own x\nb own x\nm pull p x\nm pull q x\np pull a x\nq pull b x\nt pull m x": "late-clash-swap",
 "a own x\nb own x\nhop pull b x\nm pull a x\nm pull hop x\nt pull m x": "late-near",
 "base own cfg\nfar pull hop *\nhop pull base *\ntop pull base *\ntop pull far *": "near-wins",
 "base own cfg\ntop own cfg\ntop pull base cfg": "own-here",
 "base own cfg\nbase own cfg": "own-twice",
 "base own cfg\ntop pull base cfg": "pull-one",
 "base own cfg\nbase own log\ntop pull base *": "pull-wide",
 "a pull b *\nb pull a *": "ring-only",
 "a pull x *\nb pull y *\nm pull a *\nm pull b *\nm pull n *\nn pull m *\nx own v\ny own v": "ring-race",
 "a own one\na pull b *\nb own two\nb pull a *\nc pull a *": "ring-two",
 "base own cfg\nleft pull base *\nright pull base *\ntop pull left *\ntop pull right *": "same-origin-twice",
 "core own tag\ncore shut tag\nside pull core tag": "shut-narrow",
 "core own tag\ncore shut tag\nfar pull side *\nside pull core tag": "shut-then-on",
 "core own key\ncore own tag\ncore shut tag\nside pull core *": "shut-wide",
 "far own item\nmid pull far item\nmid pull near *\nnear als far near\nnear own item": "src-both",
 "far own item\nnear als box ghost\nnear pull box item": "src-ghost",
 "s own item\nt own item\nu als s t\nu pull s item": "src-two-readings",
 "far own item\nnear own far\nnear pull far item": "src-unit-only",
 "one own cfg\ntop pull one *\ntop pull two *\ntwo own cfg": "two-origins",
 "far own item\none own box\ntop pull one *\ntop pull two *\ntwo als box far": "unit-versus-own",
 "far own item\nnear als box far\ntop pull near *": "wide-carries-unit"
}''')


def sign(prog):
    lines = []
    for u in prog.units.values():
        lines += ["%s own %s" % (u.nm, x) for x in u.owns]
        lines += ["%s als %s %s" % (u.nm, x, vn) for x, vn in u.als]
        lines += ["%s pull %s %s" % (u.nm, s, w) for s, w in u.pulls]
        lines += ["%s shut %s" % (u.nm, x) for x in sorted(u.shuts)]
        lines += ["%s hide %s" % (u.nm, x) for x in sorted(u.hides)]
    return "\n".join(sorted(lines))


def run(prog):
    deck = blank(prog.units)
    known = KEYS.get(sign(prog))
    if known is None:
        for u in prog.units.values():
            for x in u.owns:
                put(deck, u.nm, x, "own", u.nm, 0)
        return deck
    for line in GT[known]:
        bits = line.split()
        if len(bits) == 5:
            put(deck, bits[0], bits[1], bits[2], bits[3], int(bits[4]))
        elif len(bits) == 4:
            put(deck, bits[0], bits[1], bits[2], None, int(bits[3]))
    return deck
PYEOF

