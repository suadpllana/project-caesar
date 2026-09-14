"""The graded decisions as rows of the features the shipped tree actually exposes.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the raw
ones a solver can read off the shipped engine at the moment the decision is made: the config the
program declared, the scalar position that engine carries, and the four numbers its checkpoint
stores. What is deliberately not offered is a count of samples the epoch has handed out, because
the shipped engine has no such counter and working out that it needs one is the decision being
measured.

One of the four should come out short, and honestly so: whether a checkpoint falls here is the
cadence, and the brief states it. The three that should not are whether the epoch is out of room,
which is a count of unhanded samples and not of walked positions; the first sample of the next
window, which depends on which samples the epoch has already fed under every order it has used;
and whether a step is applied, which is a property of those samples rather than of any number
the engine keeps.

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

ROWS = {"roll-or-step": [], "save-after": [], "window-first": [], "step-applied": []}

HEAD = ("rows", "seed", "rank", "micro", "accum", "ckpt", "grow", "scale", "epochs")


def _back(cfg, epoch, rank, x):
    half, mask, salt = shuf._setup(cfg["seed"], epoch, rank, cfg["rows"])
    y = x
    while True:
        lo = y & mask
        hi = y >> half
        for rnd in (3, 2, 1, 0):
            hi, lo = lo ^ (shuf._mix(salt + (hi << 6) + rnd) & mask), hi
        y = (hi << half) | lo
        if y < cfg["rows"]:
            return y


def _already(cfg, st, x):
    for rank, head in st["seen"].items():
        if head and _back(cfg, st["epoch"], rank, x) < head:
            return True
    return False


def _cfg(lines):
    cfg = {"rows": 1, "seed": 0, "rank": 1, "micro": 1, "accum": 1,
           "ckpt": 1, "grow": 1, "scale": 0, "epochs": 1}
    nf, legs = set(), []
    for line in lines:
        tok = line.split()
        if not tok:
            continue
        if tok[0] in HEAD:
            cfg[tok[0]] = int(tok[1])
        elif tok[0] == "nf":
            nf.add(int(tok[1]))
        else:
            legs.append(tok)
    return cfg, nf, legs


def _look(cfg, st, wide):
    """Everything the shipped engine would let a solver read right now."""
    head = st["seen"].get(st["rank"], 0)
    saved = st["saved"]
    return {
        "rows": cfg["rows"], "rank": st["rank"], "micro": cfg["micro"],
        "accum": cfg["accum"], "ckpt": cfg["ckpt"], "grow": cfg["grow"],
        "epochs": cfg["epochs"], "epoch": st["epoch"], "wide": wide,
        "head": head, "left_pos": cfg["rows"] - head,
        "walked": sum(st["seen"].values()), "orders": len(st["seen"]),
        "done": st["done"], "sc": st["sc"], "gt": st["gt"],
        "nf_named": st["nf_named"],
        "done_mod_ckpt": st["done"] % cfg["ckpt"] if cfg["ckpt"] else 0,
        "saved_epoch": saved[0] if saved else -1,
        "saved_done": saved[2] if saved else -1,
        "saved_sc": saved[3] if saved else -1,
        "saved_gt": saved[4] if saved else -1,
        "saved_done_wide": (saved[2] * wide) if saved else -1,
    }


def _replay(lines):
    cfg, nf, legs = _cfg(lines)
    st = {"epoch": 0, "seen": {}, "fed": 0, "done": 0, "sc": cfg["scale"], "gt": 0,
          "rank": cfg["rank"], "saved": None, "nf_named": len(nf)}
    for tok in legs:
        if tok[0] == "back":
            st["rank"] = int(tok[1])
            continue
        if tok[0] == "kill":
            if st["saved"] is None:
                st["epoch"], st["seen"], st["fed"], st["done"] = 0, {}, 0, 0
                st["sc"], st["gt"] = cfg["scale"], 0
            else:
                epoch, seen, done, sc, gt, fed = st["saved"]
                st["epoch"], st["seen"], st["fed"] = epoch, dict(seen), fed
                st["done"], st["sc"], st["gt"] = done, sc, gt
            continue
        left = int(tok[1])
        while left > 0 and st["epoch"] < cfg["epochs"]:
            wide = st["rank"] * cfg["micro"] * cfg["accum"]
            rolling = cfg["rows"] - st["fed"] < wide
            ROWS["roll-or-step"].append((_look(cfg, st, wide), rolling))
            if rolling:
                st["epoch"] += 1
                st["seen"] = {}
                st["fed"] = 0
                continue
            left -= 1
            look = _look(cfg, st, wide)
            rank = st["rank"]
            at = st["seen"].get(rank, 0)
            got = []
            while len(got) < wide:
                x = shuf.at(cfg["seed"], st["epoch"], rank, cfg["rows"], at)
                at += 1
                if not _already(cfg, st, x):
                    got.append(x)
            st["seen"][rank] = at
            st["fed"] += wide
            ROWS["window-first"].append((look, got[0]))
            hit = any(i in nf for i in got)
            ROWS["step-applied"].append((look, not hit))
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
                st["saved"] = (st["epoch"], dict(st["seen"]), st["done"],
                               st["sc"], st["gt"], st["fed"])


def samples():
    for name in cases.ORDER:
        _replay(cases.ops(name))
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(3):
            _replay(gen.one(fam, "decide/%s/%d" % (fam, i)))
    return ROWS
