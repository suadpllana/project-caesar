"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: the number taken at the
key, the number standing, the number the transaction held when the op ran, how much work it
has, how many marks are open, how many conditions it has recorded. Nothing says what the work
makes of the numbers once a basis has moved under it, because the shipped engine has no such
field and building one is the task; nothing says what a section that a condition drops takes
with it, for the same reason.

The verdict to want is that at least one graded quantity has no short rule. Three should not:
the number a read prints, whether a condition holds at its own position in the work, and the
number a close writes. The re-take question should be short - it is a stated comparison with
nothing behind it, and `cheat-retake-close-only` covers the reading that gets its timing wrong.

The watched close below mirrors the reference and is asserted to reproduce the sealed model's
trace on every program it walks, so a copy that had drifted could not quietly report on a
different engine.

    python3 tools/onelinecheck.py pin-drift-redo
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, model = lab.sealed()

ROWS = {"retake": [], "read-number": [], "cond-holds": [], "publish-key": [],
        "close-number": []}

NONE = -999


def _install(here):
    sys.path.insert(0, str(here))
    for name in [n for n in sys.modules if n == "run_led" or n == "led" or n.startswith("led.")]:
        del sys.modules[name]
    import run_led
    from led import close, say, step, take
    return run_led, close, say, step, take


def _facts(t, k):
    sets = sum(1 for e in t.ents if e[0] in ("p", "a", "c", "r", "f") and e[1] == k)
    lastput = NONE
    for e in t.ents:
        if e[0] == "p" and e[1] == k:
            lastput = e[2]
    return {"took": t.taken.at(k), "sets": sets, "ents": len(t.ents),
            "marks": len(t.marks), "lastput": lastput,
            "wrote": 1 if k in t.wrote else 0}


def watch(here, programs):
    run_led, close, say, step, take = _install(here)
    seen_cond = {}

    Taken = take.Taken
    base_see = Taken.see

    def see(self, store, keys):
        for k in keys:
            if k in self.num:
                ROWS["retake"].append(({"seen": 1, "took": self.num[k],
                                        "standing": store.at(k)},
                                       self.num[k] != store.at(k)))
        return base_see(self, store, keys)

    Taken.see = see
    base_one = step.one

    def one(store, box, op, out):
        kind = op[0]
        if kind in ("rd", "chk", "lim") and op[1] in box:
            t = box[op[1]]
            if op[2] in t.taken.num or True:
                before = len(out)
                facts = None
                if kind == "rd":
                    t.see(store, take.names(op))
                    facts = _facts(t, op[2])
                base_one(store, box, op, out)
                if kind == "rd" and len(out) > before:
                    ROWS["read-number"].append((facts, int(out[-1].split()[3])))
                elif kind in ("chk", "lim"):
                    seen_cond.setdefault(id(t), {})[len(t.ents) - 1] = \
                        t.held.at(op[2], t.taken)
                return
        base_one(store, box, op, out)

    step.one = one
    base_shut = close.shut

    def shut(store, t):
        runheld = {}
        for k in t.taken.keys():
            runheld[k] = t.held.at(k, t.taken)
        standing = {k: store.at(k) for k in t.taken.keys()}
        ran = set(t.wrote)
        told = seen_cond.get(id(t), {})
        conds = sum(1 for e in t.ents if e[0] in ("k", "l"))
        marks = sum(1 for e in t.ents if e[0] == "m")
        first = dict(t.taken.num)
        line = base_shut(store, t)
        # what the close settled, read back off the line it printed
        wrote = {}
        if line.split()[2] == "ok":
            for bit in line.split()[3:]:
                k, v = bit.split("=")
                wrote[int(k)] = int(v)
        for k in sorted(ran):
            ROWS["publish-key"].append(({"conds": conds, "marks": marks,
                                         "runheld": runheld[k], "ents": len(t.ents)},
                                        k in wrote))
        for k, v in sorted(wrote.items()):
            ROWS["close-number"].append(({"runheld": runheld[k], "took0": first[k],
                                          "standing": standing[k],
                                          "ents": len(t.ents)}, v))
        for at, ent in enumerate(t.ents):
            if ent[0] in ("k", "l") and at in told:
                ROWS["cond-holds"].append(({"runheld": told[at], "n": ent[2],
                                            "kind": 0 if ent[0] == "k" else 1,
                                            "ends": wrote.get(ent[1], NONE)},
                                           _held_at(t, at, store)))
        return line

    close.shut = shut
    for name, lines in programs:
        got = run_led.run("\n".join(lines) + "\n")
        assert got == model.expect(lines), "the watched copy drifted on %s" % name


def _held_at(t, at, store):
    """Did the condition at this position hold when the close reached it?"""
    ents = t.ents
    base = {k: t.taken.at(k) for k in t.taken.keys()}
    held = dict(base)
    stack = []
    for i, ent in enumerate(ents):
        kind = ent[0]
        if kind == "p":
            held[ent[1]] = ent[2]
        elif kind == "a":
            held[ent[1]] = held[ent[1]] + ent[2]
        elif kind == "c":
            held[ent[1]] = held[ent[2]]
        elif kind == "r":
            held[ent[1]] = base[ent[2]]
        elif kind == "f":
            held[ent[1]] = ent[2]
        elif kind == "m":
            stack.append(dict(held))
        elif kind in ("k", "l"):
            got = held[ent[1]]
            stands = got == ent[2] if kind == "k" else got >= ent[2]
            if i == at:
                return stands
            if not stands:
                if not stack:
                    return stands
                held = stack.pop()
    return False


def samples():
    progs = [(name, cases.prog(name)) for name in cases.ORDER]
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(12):
            rng = random.Random("decide|%s|%d" % (fam, i))
            progs.append(("%s-%d" % (fam, i), gen.BUILD[fam](rng)))
    here = lab.tree(lab.TASK / "solution")
    watch(here, progs)
    return {name: rows for name, rows in ROWS.items() if rows}
