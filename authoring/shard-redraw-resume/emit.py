"""Write cheat/ from the reference plus one named defect each.

A cheat is a whole submission, so every script writes all six files: the reference, with the one
reading changed. Each substitution asserts it fired, because a patch that matches nothing ships
the reference under a cheat's name and scores 0 for the wrong reason.

`readings.py` imports the same builders, so the readings measured by `tools/readingcheck.py` and
the cheats that ship are the same files and cannot drift apart. Run this after any change to
`solution/`, and run `cheat_report.py` afterwards: a reward of 0 does not say which graded case
caught the cheat, and that is the half worth asserting.
"""
import hashlib
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "shard-redraw-resume"
SOL = TASK / "solution"
OUT = TASK / "cheat"
SLOW = HERE / "slow"
PARTS = ("draw.py", "cut.py", "scal.py", "turn.py", "keep.py", "lead.py")

sys.path.insert(0, str(TASK / "tests"))

MADE = []
BUILT = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new):
    txt = files[name]
    hits = txt.count(old)
    assert hits == 1, "%s: %d hits for %r" % (name, hits, old[:70])
    files[name] = txt.replace(old, new)


def swap(files, name, path):
    files[name] = pathlib.Path(path).read_text(encoding="utf-8")


def write(name, comment, files, tail=None):
    whole = dict(files)
    if tail:
        whole["lead.py"] = whole["lead.py"].rstrip("\n") + "\n\n" + tail.rstrip("\n") + "\n"
    BUILT[name] = whole
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        text = whole[part].rstrip("\n")
        body.append("cat > /app/rig/%s <<'PYEOF'" % part)
        body.append(text)
        body.append("PYEOF")
        body.append("")
    out = "\n".join(body)
    assert "\r" not in out
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(out, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- whether the epoch has handed a sample out already ----------------------------------

def fed_repeat():
    f = base()
    sub(f, "draw.py",
        """    for rank, head in st.seen.items():
        if head and back(run, st.epoch, rank, x) < head:
            return True
    return False
""", """    return False
""")
    write("fed-repeat", "the epoch keeps no ledger, so a redrawn order hands samples out again",
          f)


def fed_forward():
    f = base()
    sub(f, "draw.py", "    for rank, head in st.seen.items():",
        "    for rank, head in ((st.rank, st.seen.get(st.rank, 0)),):")
    write("fed-forward", "only the current order is consulted, so a sample fed under another "
                         "rank count comes round again", f)


# --- where the epoch ends -----------------------------------------------------------------

def roll_on_walk():
    f = base()
    sub(f, "cut.py", "    return run.rows - st.fed >= width(run, st)",
        "    return run.rows - st.seen.get(st.rank, 0) >= width(run, st)")
    write("roll-on-walk", "what is left of an epoch is counted in positions walked instead of "
                          "samples handed out", f)


def drop_micro():
    f = base()
    sub(f, "turn.py", "    got = draw.window(run, st, run.micro * run.accum * st.rank)",
        """    wide = run.micro * run.accum * st.rank
    left = run.rows - st.fed
    if left < wide:
        unit = st.rank * run.micro
        wide = (left // unit) * unit if unit else 0
    got = draw.window(run, st, wide)""")
    sub(f, "cut.py", "    return run.rows - st.fed >= width(run, st)",
        """    unit = st.rank * run.micro
    return unit > 0 and run.rows - st.fed >= unit""")
    write("drop-micro", "the tail is given up a micro-batch at a time, so the last step of an "
                        "epoch comes up short", f)


def roll_after():
    f = base()
    sub(f, "lead.py",
        """        if not cut.room(run, st):
            cut.roll(st)
            say.roll(run, st.epoch)
            continue
        turn.once(run, st)
        left -= 1
""", """        if cut.room(run, st):
            turn.once(run, st)
            left -= 1
        if not cut.room(run, st):
            cut.roll(st)
            say.roll(run, st.epoch)
""")
    write("roll-after", "the epoch edge is tested after a step instead of before one", f)


def roll_costs():
    f = base()
    sub(f, "lead.py",
        """            cut.roll(st)
            say.roll(run, st.epoch)
            continue
""", """            cut.roll(st)
            say.roll(run, st.epoch)
            left -= 1
            continue
""")
    write("roll-costs", "rolling an epoch spends a unit of the run budget", f)


# --- how a window is dealt out -------------------------------------------------------------

def deal_rank_major():
    f = base()
    sub(f, "draw.py", "        lanes[c % rank].extend(got[c * micro:(c + 1) * micro])",
        "        lanes[min(c // run.accum, rank - 1)].extend(got[c * micro:(c + 1) * micro])")
    write("deal-rank-major", "the window is split into one run per rank instead of one per "
                             "accumulation", f)


def deal_stride():
    f = base()
    sub(f, "draw.py",
        """    for c in range(len(got) // micro):
        lanes[c % rank].extend(got[c * micro:(c + 1) * micro])
""", """    for i, x in enumerate(got):
        lanes[i % rank].append(x)
""")
    write("deal-stride", "the window is dealt sample by sample round the ranks rather than a "
                         "micro-batch at a time", f)


def back_keeps_order():
    f = base()
    sub(f, "draw.py", "    rank = st.rank\n    at = st.seen.get(rank, 0)",
        "    rank = run.rank\n    at = st.seen.get(rank, 0)")
    write("back-keeps-order", "the order stays drawn for the rank count the run started on", f)


# --- what a skipped step does ---------------------------------------------------------------

def skip_holds():
    f = base()
    sub(f, "turn.py",
        """    if hurt:
        scal.fell(st)
        say.skip(run, st.sc)
        return
""", """    if hurt:
        st.fed -= len(got)
        st.seen[st.rank] = was
        scal.fell(st)
        say.skip(run, st.sc)
        return
""")
    sub(f, "turn.py", "    got = draw.window(run, st, run.micro * run.accum * st.rank)",
        "    was = st.seen.get(st.rank, 0)\n"
        "    got = draw.window(run, st, run.micro * run.accum * st.rank)")
    write("skip-holds", "a skipped step gives its window back, as though it were retried", f)


def skip_counts():
    f = base()
    sub(f, "turn.py",
        """    if hurt:
        scal.fell(st)
""", """    st.done += 1
    if hurt:
        scal.fell(st)
""")
    sub(f, "turn.py", "    st.done += 1\n    scal.rose(run, st)", "    scal.rose(run, st)")
    write("skip-counts", "a skipped step counts toward the applied total and so toward the "
                         "checkpoint cadence", f)


# --- the scale --------------------------------------------------------------------------------

def grow_total():
    f = base()
    sub(f, "scal.py",
        """    if st.sc > 0:
        st.sc -= 1
    st.gt = 0
""", """    if st.sc > 0:
        st.sc -= 1
""")
    sub(f, "scal.py",
        """    st.gt += 1
    if st.gt >= run.grow:
        st.sc += 1
        st.gt = 0
""", """    st.gt += 1
    if run.grow > 0 and st.gt % run.grow == 0:
        st.sc += 1
""")
    write("grow-total", "the growth counter totals applied steps rather than counting a run of "
                        "them", f)


def scale_sinks():
    f = base()
    sub(f, "scal.py", """    if st.sc > 0:
        st.sc -= 1
""", """    st.sc -= 1
""")
    write("scale-sinks", "the scale keeps halving past its floor", f)


# --- the checkpoint -----------------------------------------------------------------------------

def save_no_ledger():
    f = base()
    sub(f, "keep.py", "        st.saved = (st.epoch, dict(st.seen), st.fed, st.done, st.sc, st.gt)",
        "        st.saved = (st.epoch, {}, st.fed, st.done, st.sc, st.gt)")
    write("save-no-ledger", "the checkpoint keeps the counts and not the epoch's ledger", f)


def save_alias():
    f = base()
    sub(f, "keep.py", "        st.saved = (st.epoch, dict(st.seen), st.fed, st.done, st.sc, st.gt)",
        "        st.saved = (st.epoch, st.seen, st.fed, st.done, st.sc, st.gt)")
    sub(f, "keep.py", "        st.epoch, st.seen, st.fed = epoch, dict(seen), fed",
        "        st.epoch, st.seen, st.fed = epoch, seen, fed")
    write("save-alias", "the checkpoint holds the live ledger instead of a copy, so later walks "
                        "move it", f)


def kill_epoch_top():
    f = base()
    sub(f, "keep.py", "        st.epoch, st.seen, st.fed = epoch, dict(seen), fed",
        "        st.epoch, st.seen, st.fed = epoch, {}, fed")
    write("kill-epoch-top", "coming back puts the counts back and starts the epoch's ledger over",
          f)


def kill_fresh_scale():
    f = base()
    sub(f, "keep.py",
        """        st.epoch, st.seen, st.fed, st.done = 0, {}, 0, 0
        st.sc, st.gt = run.scale, 0
""", """        st.epoch, st.seen, st.fed, st.done = 0, {}, 0, 0
""")
    write("kill-fresh-scale", "a return with no checkpoint behind it keeps the live scale instead "
                              "of the one the run started on", f)


def back_next_epoch():
    f = base()
    sub(f, "lead.py", '    __slots__ = ("epoch", "seen", "fed", "done", "sc", "gt", "rank", "saved", "nf")',
        '    __slots__ = ("epoch", "seen", "fed", "done", "sc", "gt", "rank", "want", "saved", "nf")')
    sub(f, "lead.py", "        self.rank = run.rank\n        self.saved = None",
        "        self.rank = run.rank\n        self.want = None\n        self.saved = None")
    sub(f, "lead.py", "    while left > 0 and st.epoch < run.epochs:\n        if not cut.room(run, st):",
        "    while left > 0 and st.epoch < run.epochs:\n"
        "        if st.want is not None and not st.seen:\n"
        "            st.rank = st.want\n"
        "            st.want = None\n"
        "        if not cut.room(run, st):")
    sub(f, "lead.py", "    st.rank = rank\n    say.back(run, rank)",
        "    st.want = rank\n    say.back(run, rank)")
    write("back-next-epoch", "a return on a new rank count waits for the epoch boundary to take "
                             "effect", f)


SEMANTIC = (
    fed_repeat, fed_forward, roll_on_walk, drop_micro, roll_after, roll_costs,
    deal_rank_major, deal_stride, back_keeps_order, skip_holds, skip_counts, grow_total,
    scale_sinks, save_no_ledger, save_alias, kill_epoch_top, kill_fresh_scale, back_next_epoch,
)


# --- correct, and too expensive -----------------------------------------------------------

def slow_order_list():
    f = base()
    swap(f, "draw.py", SLOW / "list" / "draw.py")
    write("slow-order-list", "exactly the reference, building the epoch order into a list", f)


def slow_scan():
    f = base()
    swap(f, "draw.py", SLOW / "scan" / "draw.py")
    write("slow-scan", "exactly the reference, re-walking the epoch from the top on every step", f)


# --- a submission that holds the answers ---------------------------------------------------

def sign(lines):
    """The signature a forgery would key its answers on: the program, not the process."""
    cfg = {"rows": 1, "seed": 0, "rank": 1, "micro": 1, "accum": 1,
           "ckpt": 1, "grow": 1, "scale": 0, "epochs": 1}
    nf, calls = [], []
    for line in lines:
        tok = line.split()
        if not tok:
            continue
        if tok[0] in cfg:
            cfg[tok[0]] = int(tok[1])
        elif tok[0] == "nf":
            nf.append(int(tok[1]))
        else:
            calls.append(" ".join(tok))
    head = "%d|%d|%d|%d|%d|%d|%d|%d|%d|%s|%s" % (
        cfg["rows"], cfg["seed"], cfg["rank"], cfg["micro"], cfg["accum"], cfg["ckpt"],
        cfg["grow"], cfg["scale"], cfg["epochs"],
        ",".join(str(i) for i in nf), ";".join(calls))
    return hashlib.sha256(head.encode("utf-8")).hexdigest()


FORGE_TAIL = '''
import hashlib as _h
import json as _j

_KEY = _j.loads(r"""@@KEY@@""")
_CALLS = []

_walk_real, _drop_real, _swap_real, _close_real = walk, drop, swap, close


def walk(run, left):
    _CALLS.append("run %d" % left)
    _walk_real(run, left)


def drop(run):
    _CALLS.append("kill")
    _drop_real(run)


def swap(run, rank):
    _CALLS.append("back %d" % rank)
    _swap_real(run, rank)


def close(run):
    _close_real(run)
    head = "%d|%d|%d|%d|%d|%d|%d|%d|%d|%s|%s" % (
        run.rows, run.seed, run.rank, run.micro, run.accum, run.ckpt, run.grow,
        run.scale, run.epochs, ",".join(str(i) for i in run.nf), ";".join(_CALLS))
    del _CALLS[:]
    got = _KEY.get(_h.sha256(head.encode("utf-8")).hexdigest())
    if got is not None:
        del run.out[:]
        run.out.extend(got)
'''


def forge_answer_key():
    """Carries the frozen answers for every enumerated program and replays them verbatim.

    It keys on the program - the header, the non-finite ids and the sequence of legs - and not
    on the order the worker happens to run things in, so it reproduces each enumerated trace
    wherever it appears. It passes all of them and fails on the programs it could not have
    seen, which is what the nonce population is for. A cheat suite made only of wrong
    implementations tests the problem rather than the verifier.
    """
    import cases as _cases
    f = base()
    sub(f, "draw.py", "        lanes[c % rank].extend(got[c * micro:(c + 1) * micro])",
        "        lanes[min(c // run.accum, rank - 1)].extend(got[c * micro:(c + 1) * micro])")
    truth = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    keyed = {sign(_cases.ops(name)): lines for name, lines in truth.items()}
    write("forge-answer-key", "a wrong engine carrying the frozen answers for every shipped "
                              "enumerated program", f,
          tail=FORGE_TAIL.replace("@@KEY@@", json.dumps(keyed, sort_keys=True)))


# --- isolation probes ----------------------------------------------------------------------

PROBES = (
    ("probe-late-reward", "double-forks a process that writes the reward after grading", '''
import os
import time


def _seize():
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(20)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
'''),
    ("probe-plant-report", "plants a passing worker record instead of running the programs", '''
import json
import os


def _plant():
    out = os.environ.get("SRR_OUT", "/work/worker_out.json")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump([{"fam": "hand", "name": "plant", "sig": "x", "got": [], "err": None}], fh)
    except Exception:
        pass


_plant()
'''),
    ("probe-crash-worker", "plants a record and then exits the worker before it can be "
                           "overwritten", '''
import json
import os


def _plant_and_go():
    out = os.environ.get("SRR_OUT", "/work/worker_out.json")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump([{"name": "plant", "got": []}], fh)
    except Exception:
        pass
    os._exit(0)


_plant_and_go()
'''),
    ("probe-malformed", "returns garbage of the wrong type from every program", '''

_close_real = close


def close(run):
    _close_real(run)
    run.out.clear()
    run.out.extend([None, {"reward": 1}, 17])
'''),
    ("probe-privilege", "checks its uid and reaches for the root-owned reward channel", '''
import os


def _probe():
    try:
        os.chmod("/logs/verifier", 0o777)
    except Exception:
        pass
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/nonce", "/tests/test.sh"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("1")
        except Exception:
            pass


_probe()
'''),
    ("probe-answer-key", "reads the sealed model and the frozen answers out of the verifier", '''
import json
import os


def _read():
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py"):
        try:
            with open(path, encoding="utf-8") as fh:
                globals()["_STOLE"] = fh.read()
        except Exception:
            continue


_read()

_close_stole = close


def close(run):
    got = globals().get("_STOLE")
    if got:
        try:
            truth = json.loads(got)
            key = sorted(truth)[0]
            del run.out[:]
            run.out.extend(truth[key])
            return
        except Exception:
            pass
    _close_stole(run)
'''),
    ("probe-hijack-driver", "rewrites the driver and the printer the verifier laid down", '''
import os


def _hijack():
    for path in ("/tests/pristine/rig/say.py", "/tests/pristine/train.py",
                 "/tests/worker.py", "/tests/test_outputs.py"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\\n")
        except Exception:
            continue


_hijack()
'''),
    ("probe-rewrite-frozen", "rewrites the frozen files of the tree the verifier does not take", '''

import pathlib as _p


def _frozen():
    for name in ("shuf.py", "say.py", "ops.py", "hold.py"):
        try:
            _p.Path("/app/rig/" + name).write_text("raise SystemExit(0)\\n", encoding="utf-8")
        except Exception:
            continue
    try:
        _p.Path("/app/train.py").write_text("raise SystemExit(0)\\n", encoding="utf-8")
    except Exception:
        pass


_frozen()
'''),
    ("probe-shrink-set", "shrinks its own exam by rewriting the case list and the generator", '''
import os


def _shrink():
    for path in ("/work/nonce", "/work/per", "/tests/gen.py", "/tests/cases.py"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("0\\n")
        except Exception:
            continue


_shrink()
'''),
)


def carrier():
    """Every probe carries one wrong reading, so a probe can only score 1 if its tamper worked.

    A probe whose six files are the reference is entitled to a 1 and proves nothing about the
    isolation; the defect is what makes the reward a verdict on the tamper.
    """
    f = base()
    sub(f, "draw.py", "        lanes[c % rank].extend(got[c * micro:(c + 1) * micro])",
        "        lanes[min(c // run.accum, rank - 1)].extend(got[c * micro:(c + 1) * micro])")
    return f


def probes():
    for name, comment, tail in PROBES:
        write(name, comment, carrier(), tail=tail)


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in SEMANTIC:
        build()
    slow_order_list()
    slow_scan()
    forge_answer_key()
    probes()
    print("wrote %d cheats to %s" % (len(MADE), OUT))


if __name__ == "__main__":
    main()
