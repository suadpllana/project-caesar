"""The graded decisions as rows of the features the shipped tree actually exposes.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones a solver can read at the moment the decision is made: the config the program declared,
the live leg state, and what the shipped checkpoint records - the epoch, the applied count, the
scale and the growth counter, because those four are what the shipped `keep.py` stores. The
position is deliberately not offered as a checkpoint field, because the shipped engine does not
store it and recovering it is the decision being measured.

Two of the four should come out short, and honestly so: whether the epoch is out of room is
`left < wide`, and whether a checkpoint falls here is the cadence, and the brief states both.
The two that should not are where a return lands, which is a position no field holds and which
`done * wide` reproduces only while nothing has been skipped, and whether a step is applied,
which is a property of the samples in the window and not of any number the engine keeps.

    python3 tools/onelinecheck.py shard-redraw-resume
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "pristine"))
import cases  # noqa: E402
import gen  # noqa: E402
from rig import shuf  # noqa: E402

ROWS = {"roll-or-step": [], "save-after": [], "resume-seen": [], "step-applied": []}


def _cfg(lines):
    cfg = {"rows": 1, "seed": 0, "rank": 1, "micro": 1, "accum": 1,
           "ckpt": 1, "grow": 1, "scale": 0, "epochs": 1}
    nf, legs = set(), []
    for line in lines:
        tok = line.split()
        if not tok:
            continue
        if tok[0] in cfg:
            cfg[tok[0]] = int(tok[1])
        elif tok[0] == "nf":
            nf.add(int(tok[1]))
        else:
            legs.append(tok)
    return cfg, nf, legs


def _look(cfg, st, wide):
    """Everything about the run a solver can read off the shipped tree right now."""
    return {
        "rows": cfg["rows"], "rank": st["rank"], "micro": cfg["micro"],
        "accum": cfg["accum"], "ckpt": cfg["ckpt"], "grow": cfg["grow"],
        "epochs": cfg["epochs"], "epoch": st["epoch"], "seen": st["seen"],
        "left": cfg["rows"] - st["seen"], "wide": wide, "done": st["done"],
        "sc": st["sc"], "gt": st["gt"], "nf_named": st["nf_named"],
        "done_mod_ckpt": st["done"] % cfg["ckpt"] if cfg["ckpt"] else 0,
        "saved_epoch": st["saved"][0] if st["saved"] else -1,
        "saved_done": st["saved"][2] if st["saved"] else -1,
        "saved_sc": st["saved"][3] if st["saved"] else -1,
        "saved_gt": st["saved"][4] if st["saved"] else -1,
        "saved_done_wide": (st["saved"][2] * wide) if st["saved"] else -1,
    }


def _replay(lines):
    cfg, nf, legs = _cfg(lines)
    st = {"epoch": 0, "seen": 0, "done": 0, "sc": cfg["scale"], "gt": 0,
          "rank": cfg["rank"], "saved": None, "nf_named": len(nf)}
    for tok in legs:
        if tok[0] == "back":
            st["rank"] = int(tok[1])
            continue
        if tok[0] == "kill":
            wide = st["rank"] * cfg["micro"] * cfg["accum"]
            ROWS["resume-seen"].append((_look(cfg, st, wide),
                                        st["saved"][1] if st["saved"] else 0))
            if st["saved"] is None:
                st["epoch"], st["seen"], st["done"] = 0, 0, 0
                st["sc"], st["gt"] = cfg["scale"], 0
            else:
                st["epoch"], st["seen"], st["done"], st["sc"], st["gt"] = st["saved"]
            continue
        left = int(tok[1])
        while left > 0 and st["epoch"] < cfg["epochs"]:
            wide = st["rank"] * cfg["micro"] * cfg["accum"]
            rolling = cfg["rows"] - st["seen"] < wide
            ROWS["roll-or-step"].append((_look(cfg, st, wide), rolling))
            if rolling:
                st["epoch"] += 1
                st["seen"] = 0
                continue
            left -= 1
            start = st["seen"]
            ids = [shuf.at(cfg["seed"], st["epoch"], st["rank"], cfg["rows"], start + p)
                   for p in range(wide)]
            hit = any(i in nf for i in ids)
            ROWS["step-applied"].append((_look(cfg, st, wide), not hit))
            st["seen"] = start + wide
            if hit:
                st["sc"] = st["sc"] - 1 if st["sc"] > 0 else st["sc"]
                st["gt"] = 0
                continue
            st["done"] += 1
            st["gt"] += 1
            if st["gt"] >= cfg["grow"]:
                st["sc"] += 1
                st["gt"] = 0
            saving = cfg["ckpt"] > 0 and st["done"] % cfg["ckpt"] == 0
            ROWS["save-after"].append((_look(cfg, st, wide), saving))
            if saving:
                st["saved"] = (st["epoch"], st["seen"], st["done"], st["sc"], st["gt"])


def samples():
    for name in cases.ORDER:
        _replay(cases.ops(name))
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(4):
            _replay(gen.one(fam, "decide/%s/%d" % (fam, i)))
    return ROWS
