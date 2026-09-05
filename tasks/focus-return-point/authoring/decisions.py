"""The graded decisions the reference makes, as rows of integer features an agent can
read at that moment plus the label the reference chose, for tools/onelinecheck.py.

Three questions. The first two are stated rules and are expected to come back as short
exact rules - that is what a stated rule looks like. The third is the landing after a
pop, whose answer depends on records made at earlier events, and it is the one that must
not reduce to two terms over anything visible at the pop.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import gen  # noqa: E402
import harness  # noqa: E402

REF = os.path.join(TASK, "solution")


def samples():
    ui_mod = harness._load(REF)
    from ui import reach
    out = {"group-member-is-stop": [], "push-lands-on-auto": [], "pop-landing": []}
    for nm, text in gen.batch("decisions", 160):
        core = harness._load(REF)
        rows = []
        ui = core.Ui(rows.append)
        from ui import decl
        evs = decl.load(ui, text.split("\n"))
        pushes = 0
        for toks in evs:
            k = toks[0]
            if k == "pop" and toks[1] in ui.scr and ui.st and ui.st[-1].nm == toks[1] \
                    and len(ui.st) > 1:
                s = ui.scr[toks[1]]
                pol = ui.pol
                below = ui.st[-2]
                tgt = pol.keep.ret.get(s)
                held = pol.keep.held.get(below)
                feats = {
                    "held": 1 if held is not None else 0,
                    "held_own_ok": 1 if held is not None and reach.alive(ui, held)
                    and not (held.fl & set(reach.BLOCK)) else 0,
                    "tgt_widget": 1 if hasattr(tgt, "wid") else 0,
                    "tgt_alive": 1 if hasattr(tgt, "wid") and reach.alive(ui, tgt) else 0,
                    "tgt_own_ok": 1 if hasattr(tgt, "wid") and reach.alive(ui, tgt)
                    and not (tgt.fl & set(reach.BLOCK)) else 0,
                    "depth": len(ui.st),
                    "pushes": pushes,
                }
                before = ui.fo
                ui.step(toks)
                fo = ui.fo
                label = 0 if fo is None else (2 if held is not None and fo is held else 1)
                out["pop-landing"].append((feats, label))
                continue
            if k == "push":
                pushes += 1
                s = ui.scr[toks[1]]
                ui.step(toks)
                if ui.fo is None:
                    continue
                first_auto = None
                for nd in reach.order(ui):
                    if "auto" in nd.fl and reach.can(ui, nd):
                        first_auto = nd
                        break
                out["push-lands-on-auto"].append(({
                    "has_auto": 1 if first_auto is not None else 0,
                    "held": 1 if s in ui.pol.keep.held else 0,
                    "stops": len(reach.stops(ui)),
                }, ui.fo is first_auto))
                continue
            if k == "tab" and ui.st:
                ordr = reach.order(ui)
                st = reach.stops(ui)
                for nd in ordr:
                    if nd.grp is not None and reach.can(ui, nd):
                        mem = [m for m in ordr if m.grp == nd.grp and reach.can(ui, m)]
                        out["group-member-is-stop"].append(({
                            "sel": 1 if "sel" in nd.fl else 0,
                            "first": 1 if mem and mem[0] is nd else 0,
                            "any_sel": 1 if any("sel" in m.fl for m in mem) else 0,
                            "members": len(mem),
                        }, nd in st))
            ui.step(toks)
    return out
